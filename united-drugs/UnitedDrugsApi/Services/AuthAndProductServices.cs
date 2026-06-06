using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using UnitedDrugsApi.Configuration;
using UnitedDrugsApi.Contracts;
using UnitedDrugsApi.Domain;
using UnitedDrugsApi.Infrastructure.Auth;
using UnitedDrugsApi.Infrastructure.Persistence;

namespace UnitedDrugsApi.Services;

public interface IAuthService
{
    Task<AuthResponse> LoginAsync(LoginRequest request, CancellationToken cancellationToken);
    Task<AuthResponse> RefreshAsync(RefreshRequest request, CancellationToken cancellationToken);
}

public sealed class AuthService(
    AppDbContext dbContext,
    IPasswordHasher passwordHasher,
    IJwtTokenService jwtTokenService,
    IOptions<JwtOptions> jwtOptions) : IAuthService
{
    private readonly JwtOptions _jwtOptions = jwtOptions.Value;

    public async Task<AuthResponse> LoginAsync(LoginRequest request, CancellationToken cancellationToken)
    {
        var user = await dbContext.Users.SingleOrDefaultAsync(x => x.Username == request.Username, cancellationToken)
            ?? throw new InvalidOperationException("Invalid username or password.");

        if (!user.IsActive || !passwordHasher.Verify(request.Password, user.PasswordHash))
        {
            throw new InvalidOperationException("Invalid username or password.");
        }

        return await IssueTokensAsync(user, cancellationToken);
    }

    public async Task<AuthResponse> RefreshAsync(RefreshRequest request, CancellationToken cancellationToken)
    {
        var candidates = await dbContext.RefreshTokens.Include(x => x.User)
            .Where(x => x.RevokedAtUtc == null && x.ExpiresAtUtc > DateTime.UtcNow)
            .ToListAsync(cancellationToken);

        var match = candidates.SingleOrDefault(x => BCrypt.Net.BCrypt.Verify(request.RefreshToken, x.TokenHash))
            ?? throw new InvalidOperationException("Invalid refresh token.");

        match.RevokedAtUtc = DateTime.UtcNow;
        await dbContext.SaveChangesAsync(cancellationToken);

        return await IssueTokensAsync(match.User, cancellationToken);
    }

    private async Task<AuthResponse> IssueTokensAsync(User user, CancellationToken cancellationToken)
    {
        var accessToken = jwtTokenService.CreateAccessToken(user);
        var refreshToken = jwtTokenService.CreateRefreshToken();

        dbContext.RefreshTokens.Add(new RefreshToken
        {
            UserId = user.Id,
            TokenHash = passwordHasher.Hash(refreshToken),
            ExpiresAtUtc = DateTime.UtcNow.AddDays(_jwtOptions.RefreshTokenDays),
        });

        await dbContext.SaveChangesAsync(cancellationToken);
        return new AuthResponse(accessToken, refreshToken, user.Username, user.Role);
    }
}

public interface IProductService
{
    Task<List<ProductResponse>> ListAsync(CancellationToken cancellationToken);
    Task<ProductResponse> GetAsync(Guid id, CancellationToken cancellationToken);
    Task<ProductResponse> CreateAsync(ProductCreateRequest request, Guid? actorId, CancellationToken cancellationToken);
    Task<ProductResponse> UpdateAsync(Guid id, ProductUpdateRequest request, CancellationToken cancellationToken);
    Task<List<ProductResponse>> GetLowStockAsync(decimal threshold, CancellationToken cancellationToken);
    Task<List<ProductResponse>> GetExpiringAsync(int days, CancellationToken cancellationToken);
}

public sealed class ProductService(AppDbContext dbContext) : IProductService
{
    public async Task<List<ProductResponse>> ListAsync(CancellationToken cancellationToken) =>
        await QueryProducts().ToListAsync(cancellationToken);

    public async Task<ProductResponse> GetAsync(Guid id, CancellationToken cancellationToken) =>
        await QueryProducts().SingleAsync(x => x.Id == id, cancellationToken);

    public async Task<ProductResponse> CreateAsync(ProductCreateRequest request, Guid? actorId, CancellationToken cancellationToken)
    {
        var product = new Product
        {
            RegNo = request.RegNo,
            BatchNo = request.BatchNo,
            MfgDate = request.MfgDate,
            ExpDate = request.ExpDate,
            ProductDescription = request.ProductDescription,
            TradePrice = request.TradePrice,
            DiscountPercent = request.DiscountPercent,
        };

        dbContext.Products.Add(product);
        dbContext.InventoryStocks.Add(new InventoryStock
        {
            ProductId = product.Id,
            QuantityOnHand = request.OpeningQuantity,
        });

        if (request.OpeningQuantity > 0)
        {
            dbContext.StockMovements.Add(new StockMovement
            {
                ProductId = product.Id,
                MovementType = "stock_in",
                Quantity = request.OpeningQuantity,
                ReferenceType = "product_opening",
                ReferenceId = product.Id.ToString(),
                Notes = "Opening stock",
                CreatedByUserId = actorId,
            });
        }

        await dbContext.SaveChangesAsync(cancellationToken);
        return await GetAsync(product.Id, cancellationToken);
    }

    public async Task<ProductResponse> UpdateAsync(Guid id, ProductUpdateRequest request, CancellationToken cancellationToken)
    {
        var product = await dbContext.Products.SingleAsync(x => x.Id == id, cancellationToken);
        product.RegNo = request.RegNo;
        product.BatchNo = request.BatchNo;
        product.MfgDate = request.MfgDate;
        product.ExpDate = request.ExpDate;
        product.ProductDescription = request.ProductDescription;
        product.TradePrice = request.TradePrice;
        product.DiscountPercent = request.DiscountPercent;
        product.UpdatedAtUtc = DateTime.UtcNow;

        await dbContext.SaveChangesAsync(cancellationToken);
        return await GetAsync(id, cancellationToken);
    }

    public async Task<List<ProductResponse>> GetLowStockAsync(decimal threshold, CancellationToken cancellationToken) =>
        await QueryProducts().Where(x => x.QuantityOnHand < threshold).ToListAsync(cancellationToken);

    public async Task<List<ProductResponse>> GetExpiringAsync(int days, CancellationToken cancellationToken)
    {
        var target = DateOnly.FromDateTime(DateTime.UtcNow.Date.AddDays(days));
        var today = DateOnly.FromDateTime(DateTime.UtcNow.Date);
        return await QueryProducts()
            .Where(x => x.ExpDate != null && x.ExpDate >= today && x.ExpDate <= target)
            .ToListAsync(cancellationToken);
    }

    private IQueryable<ProductResponse> QueryProducts() =>
        dbContext.Products.AsNoTracking()
            .Select(x => new ProductResponse(
                x.Id,
                x.RegNo,
                x.BatchNo,
                x.MfgDate,
                x.ExpDate,
                x.ProductDescription,
                x.TradePrice,
                x.DiscountPercent,
                x.InventoryStock != null ? x.InventoryStock.QuantityOnHand : 0));
}
