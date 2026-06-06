using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using UnitedDrugsApi.Contracts;
using UnitedDrugsApi.Services;

namespace UnitedDrugsApi.Controllers;

[ApiController]
[Route("api/auth")]
public class AuthController(IAuthService authService) : ControllerBase
{
    [HttpPost("login")]
    [AllowAnonymous]
    public async Task<ActionResult<AuthResponse>> Login([FromBody] LoginRequest request, CancellationToken cancellationToken)
    {
        var response = await authService.LoginAsync(request, cancellationToken);
        return Ok(response);
    }

    [HttpPost("refresh")]
    [AllowAnonymous]
    public async Task<ActionResult<AuthResponse>> Refresh([FromBody] RefreshRequest request, CancellationToken cancellationToken)
    {
        var response = await authService.RefreshAsync(request, cancellationToken);
        return Ok(response);
    }
}

[ApiController]
[Authorize]
[Route("api/products")]
public class ProductsController(IProductService productService) : ControllerBase
{
    [HttpGet]
    public Task<List<ProductResponse>> GetAll(CancellationToken cancellationToken) =>
        productService.ListAsync(cancellationToken);

    [HttpGet("{id:guid}")]
    public Task<ProductResponse> Get(Guid id, CancellationToken cancellationToken) =>
        productService.GetAsync(id, cancellationToken);

    [HttpPost]
    public Task<ProductResponse> Create([FromBody] ProductCreateRequest request, CancellationToken cancellationToken) =>
        productService.CreateAsync(request, GetUserId(), cancellationToken);

    [HttpPut("{id:guid}")]
    public Task<ProductResponse> Update(Guid id, [FromBody] ProductUpdateRequest request, CancellationToken cancellationToken) =>
        productService.UpdateAsync(id, request, cancellationToken);

    [HttpGet("low-stock")]
    public Task<List<ProductResponse>> GetLowStock([FromQuery] decimal threshold = 10, CancellationToken cancellationToken = default) =>
        productService.GetLowStockAsync(threshold, cancellationToken);

    [HttpGet("expiring")]
    public Task<List<ProductResponse>> GetExpiring([FromQuery] int days = 7, CancellationToken cancellationToken = default) =>
        productService.GetExpiringAsync(days, cancellationToken);

    private Guid? GetUserId() =>
        Guid.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out var userId) ? userId : null;
}

[ApiController]
[Authorize]
[Route("api/inventory")]
public class InventoryController(IInventoryService inventoryService) : ControllerBase
{
    [HttpGet]
    public Task<List<ProductResponse>> Get(CancellationToken cancellationToken) =>
        inventoryService.ListAsync(cancellationToken);

    [HttpPost("stock-in")]
    public Task<ProductResponse> StockIn([FromBody] StockInRequest request, CancellationToken cancellationToken) =>
        inventoryService.StockInAsync(request, GetUserId(), cancellationToken);

    [HttpPost("adjust")]
    public Task<ProductResponse> Adjust([FromBody] StockAdjustRequest request, CancellationToken cancellationToken) =>
        inventoryService.AdjustAsync(request, GetUserId(), cancellationToken);

    private Guid? GetUserId() =>
        Guid.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out var userId) ? userId : null;
}

[ApiController]
[Authorize]
[Route("api/invoices")]
public class InvoicesController(IInvoiceService invoiceService) : ControllerBase
{
    [HttpGet]
    public Task<List<InvoiceListItemResponse>> Get(CancellationToken cancellationToken) =>
        invoiceService.ListAsync(cancellationToken);

    [HttpPost]
    public Task<InvoiceListItemResponse> Create([FromBody] CreateInvoiceRequest request, CancellationToken cancellationToken) =>
        invoiceService.CreateAsync(request, GetUserId(), cancellationToken);

    private Guid? GetUserId() =>
        Guid.TryParse(User.FindFirstValue(ClaimTypes.NameIdentifier), out var userId) ? userId : null;
}

[ApiController]
[Authorize]
[Route("api/reports")]
public class ReportsController(IReportsService reportsService) : ControllerBase
{
    [HttpGet("sales-summary")]
    public Task<SalesSummaryResponse> Summary(CancellationToken cancellationToken) =>
        reportsService.GetSummaryAsync(cancellationToken);

    [HttpGet("sales-daily")]
    public Task<List<SalesPointResponse>> Daily([FromQuery] int days = 7, CancellationToken cancellationToken = default) =>
        reportsService.GetDailyAsync(days, cancellationToken);

    [HttpGet("sales-monthly")]
    public Task<List<SalesPointResponse>> Monthly([FromQuery] int months = 6, CancellationToken cancellationToken = default) =>
        reportsService.GetMonthlyAsync(months, cancellationToken);

    [HttpGet("top-customers")]
    public Task<List<TopCustomerResponse>> TopCustomers([FromQuery] int limit = 5, CancellationToken cancellationToken = default) =>
        reportsService.GetTopCustomersAsync(limit, cancellationToken);

    [HttpGet("recent-sales")]
    public Task<List<InvoiceListItemResponse>> RecentSales([FromQuery] int limit = 10, CancellationToken cancellationToken = default) =>
        reportsService.GetRecentSalesAsync(limit, cancellationToken);
}
