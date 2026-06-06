using Microsoft.EntityFrameworkCore;
using UnitedDrugsApi.Contracts;
using UnitedDrugsApi.Domain;
using UnitedDrugsApi.Infrastructure.Persistence;

namespace UnitedDrugsApi.Services;

public interface IInventoryService
{
    Task<List<ProductResponse>> ListAsync(CancellationToken cancellationToken);
    Task<ProductResponse> StockInAsync(StockInRequest request, Guid? actorId, CancellationToken cancellationToken);
    Task<ProductResponse> AdjustAsync(StockAdjustRequest request, Guid? actorId, CancellationToken cancellationToken);
}

public sealed class InventoryService(AppDbContext dbContext, IProductService productService) : IInventoryService
{
    public Task<List<ProductResponse>> ListAsync(CancellationToken cancellationToken) =>
        productService.ListAsync(cancellationToken);

    public async Task<ProductResponse> StockInAsync(StockInRequest request, Guid? actorId, CancellationToken cancellationToken)
    {
        if (request.Quantity <= 0) throw new InvalidOperationException("Quantity must be greater than zero.");

        var stock = await dbContext.InventoryStocks.SingleAsync(x => x.ProductId == request.ProductId, cancellationToken);
        stock.QuantityOnHand += request.Quantity;
        stock.UpdatedAtUtc = DateTime.UtcNow;

        dbContext.StockMovements.Add(new StockMovement
        {
            ProductId = request.ProductId,
            MovementType = "stock_in",
            Quantity = request.Quantity,
            ReferenceType = "manual_stock_in",
            ReferenceId = Guid.NewGuid().ToString(),
            Notes = request.Notes,
            CreatedByUserId = actorId,
        });

        await dbContext.SaveChangesAsync(cancellationToken);
        return await productService.GetAsync(request.ProductId, cancellationToken);
    }

    public async Task<ProductResponse> AdjustAsync(StockAdjustRequest request, Guid? actorId, CancellationToken cancellationToken)
    {
        var stock = await dbContext.InventoryStocks.SingleAsync(x => x.ProductId == request.ProductId, cancellationToken);
        stock.QuantityOnHand = request.Quantity;
        stock.UpdatedAtUtc = DateTime.UtcNow;

        dbContext.StockMovements.Add(new StockMovement
        {
            ProductId = request.ProductId,
            MovementType = "adjustment",
            Quantity = request.Quantity,
            ReferenceType = "manual_adjustment",
            ReferenceId = Guid.NewGuid().ToString(),
            Notes = request.Notes,
            CreatedByUserId = actorId,
        });

        await dbContext.SaveChangesAsync(cancellationToken);
        return await productService.GetAsync(request.ProductId, cancellationToken);
    }
}

public interface IInvoiceService
{
    Task<List<InvoiceListItemResponse>> ListAsync(CancellationToken cancellationToken);
    Task<InvoiceListItemResponse> CreateAsync(CreateInvoiceRequest request, Guid? actorId, CancellationToken cancellationToken);
}

public sealed class InvoiceService(AppDbContext dbContext) : IInvoiceService
{
    public async Task<List<InvoiceListItemResponse>> ListAsync(CancellationToken cancellationToken) =>
        await dbContext.Invoices.AsNoTracking()
            .OrderByDescending(x => x.CreatedAtUtc)
            .Select(x => new InvoiceListItemResponse(
                x.Id,
                x.BillNo,
                x.StrNo,
                x.NtnNo,
                x.CustomerName,
                x.InvoiceDate,
                x.OrderDate,
                x.TotalQuantity,
                x.CreatedAtUtc))
            .ToListAsync(cancellationToken);

    public async Task<InvoiceListItemResponse> CreateAsync(CreateInvoiceRequest request, Guid? actorId, CancellationToken cancellationToken)
    {
        if (request.Items.Count == 0) throw new InvalidOperationException("At least one invoice item is required.");

        await using var transaction = await dbContext.Database.BeginTransactionAsync(cancellationToken);

        var productIds = request.Items.Select(x => x.ProductId).Distinct().ToList();
        var stocks = await dbContext.InventoryStocks
            .Where(x => productIds.Contains(x.ProductId))
            .ToDictionaryAsync(x => x.ProductId, cancellationToken);

        foreach (var item in request.Items)
        {
            if (!stocks.TryGetValue(item.ProductId, out var stock))
            {
                throw new InvalidOperationException($"Product {item.ProductId} was not found in inventory.");
            }
            if (item.Quantity <= 0)
            {
                throw new InvalidOperationException("Invoice item quantity must be greater than zero.");
            }
            if (stock.QuantityOnHand < item.Quantity)
            {
                throw new InvalidOperationException($"Insufficient stock for product {item.ProductId}.");
            }
        }

        var invoice = new Invoice
        {
            InvoiceNo = request.BillNo,
            BillNo = request.BillNo,
            StrNo = request.StrNo,
            NtnNo = request.NtnNo,
            DeliveryChallanNo = request.DeliveryChallanNo,
            OrderContractNo = request.OrderContractNo,
            OrderDate = request.OrderDate,
            InspectionNoteNo = request.InspectionNoteNo,
            InvoiceDate = request.InvoiceDate,
            ToText = request.ToText,
            CustomerName = request.ToText.Split(Environment.NewLine, StringSplitOptions.None).FirstOrDefault() ?? string.Empty,
            TotalQuantity = request.Items.Sum(x => x.Quantity),
            CreatedByUserId = actorId,
        };

        dbContext.Invoices.Add(invoice);

        var products = await dbContext.Products
            .Where(x => productIds.Contains(x.Id))
            .ToDictionaryAsync(x => x.Id, cancellationToken);

        foreach (var item in request.Items)
        {
            var product = products[item.ProductId];
            dbContext.InvoiceItems.Add(new InvoiceItem
            {
                InvoiceId = invoice.Id,
                ProductId = product.Id,
                ProductDescription = product.ProductDescription,
                Quantity = item.Quantity,
                UnitPrice = item.UnitPrice,
            });

            stocks[item.ProductId].QuantityOnHand -= item.Quantity;
            stocks[item.ProductId].UpdatedAtUtc = DateTime.UtcNow;

            dbContext.StockMovements.Add(new StockMovement
            {
                ProductId = item.ProductId,
                MovementType = "sale",
                Quantity = item.Quantity,
                ReferenceType = "invoice",
                ReferenceId = invoice.Id.ToString(),
                Notes = $"Invoice {request.BillNo}",
                CreatedByUserId = actorId,
            });
        }

        await dbContext.SaveChangesAsync(cancellationToken);
        await transaction.CommitAsync(cancellationToken);

        return new InvoiceListItemResponse(
            invoice.Id,
            invoice.BillNo,
            invoice.StrNo,
            invoice.NtnNo,
            invoice.CustomerName,
            invoice.InvoiceDate,
            invoice.OrderDate,
            invoice.TotalQuantity,
            invoice.CreatedAtUtc);
    }
}

public interface IReportsService
{
    Task<SalesSummaryResponse> GetSummaryAsync(CancellationToken cancellationToken);
    Task<List<SalesPointResponse>> GetDailyAsync(int days, CancellationToken cancellationToken);
    Task<List<SalesPointResponse>> GetMonthlyAsync(int months, CancellationToken cancellationToken);
    Task<List<TopCustomerResponse>> GetTopCustomersAsync(int limit, CancellationToken cancellationToken);
    Task<List<InvoiceListItemResponse>> GetRecentSalesAsync(int limit, CancellationToken cancellationToken);
}

public sealed class ReportsService(AppDbContext dbContext, IInvoiceService invoiceService) : IReportsService
{
    public async Task<SalesSummaryResponse> GetSummaryAsync(CancellationToken cancellationToken)
    {
        var invoices = dbContext.Invoices.AsNoTracking();
        var totalInvoices = await invoices.CountAsync(cancellationToken);
        var totalQuantity = await invoices.SumAsync(x => (decimal?)x.TotalQuantity, cancellationToken) ?? 0;
        return new SalesSummaryResponse(totalInvoices, totalQuantity, totalInvoices == 0 ? 0 : totalQuantity / totalInvoices);
    }

    public async Task<List<SalesPointResponse>> GetDailyAsync(int days, CancellationToken cancellationToken)
    {
        var threshold = DateOnly.FromDateTime(DateTime.UtcNow.Date.AddDays(-days + 1));
        return await dbContext.Invoices.AsNoTracking()
            .Where(x => x.InvoiceDate != null && x.InvoiceDate >= threshold)
            .GroupBy(x => x.InvoiceDate!.Value)
            .OrderBy(x => x.Key)
            .Select(x => new SalesPointResponse(x.Key.ToString("yyyy-MM-dd"), x.Sum(y => y.TotalQuantity), x.Count()))
            .ToListAsync(cancellationToken);
    }

    public async Task<List<SalesPointResponse>> GetMonthlyAsync(int months, CancellationToken cancellationToken)
    {
        var cutoff = DateTime.UtcNow.AddMonths(-months + 1);
        return await dbContext.Invoices.AsNoTracking()
            .Where(x => x.CreatedAtUtc >= cutoff)
            .GroupBy(x => new { x.CreatedAtUtc.Year, x.CreatedAtUtc.Month })
            .OrderBy(x => x.Key.Year).ThenBy(x => x.Key.Month)
            .Select(x => new SalesPointResponse($"{x.Key.Year}-{x.Key.Month:00}", x.Sum(y => y.TotalQuantity), x.Count()))
            .ToListAsync(cancellationToken);
    }

    public async Task<List<TopCustomerResponse>> GetTopCustomersAsync(int limit, CancellationToken cancellationToken) =>
        await dbContext.Invoices.AsNoTracking()
            .GroupBy(x => x.CustomerName)
            .OrderByDescending(x => x.Sum(y => y.TotalQuantity))
            .Take(limit)
            .Select(x => new TopCustomerResponse(x.Key, x.Sum(y => y.TotalQuantity), x.Count()))
            .ToListAsync(cancellationToken);

    public async Task<List<InvoiceListItemResponse>> GetRecentSalesAsync(int limit, CancellationToken cancellationToken) =>
        (await invoiceService.ListAsync(cancellationToken)).Take(limit).ToList();
}
