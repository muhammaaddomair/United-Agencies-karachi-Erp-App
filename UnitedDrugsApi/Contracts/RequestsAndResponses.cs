namespace UnitedDrugsApi.Contracts;

public record LoginRequest(string Username, string Password);
public record RefreshRequest(string RefreshToken);
public record AuthResponse(string AccessToken, string RefreshToken, string Username, string Role);

public record ProductCreateRequest(
    string RegNo,
    string BatchNo,
    DateOnly? MfgDate,
    DateOnly? ExpDate,
    string ProductDescription,
    decimal TradePrice,
    decimal DiscountPercent,
    decimal OpeningQuantity);

public record ProductUpdateRequest(
    string RegNo,
    string BatchNo,
    DateOnly? MfgDate,
    DateOnly? ExpDate,
    string ProductDescription,
    decimal TradePrice,
    decimal DiscountPercent);

public record ProductResponse(
    Guid Id,
    string RegNo,
    string BatchNo,
    DateOnly? MfgDate,
    DateOnly? ExpDate,
    string ProductDescription,
    decimal TradePrice,
    decimal DiscountPercent,
    decimal QuantityOnHand);

public record StockInRequest(Guid ProductId, decimal Quantity, string Notes);
public record StockAdjustRequest(Guid ProductId, decimal Quantity, string Notes);

public record InvoiceLineRequest(Guid ProductId, decimal Quantity, decimal UnitPrice);

public record CreateInvoiceRequest(
    string BillNo,
    string StrNo,
    string NtnNo,
    string DeliveryChallanNo,
    string OrderContractNo,
    DateOnly? OrderDate,
    string InspectionNoteNo,
    DateOnly? InvoiceDate,
    string ToText,
    List<InvoiceLineRequest> Items);

public record InvoiceListItemResponse(
    Guid Id,
    string BillNo,
    string StrNo,
    string NtnNo,
    string CustomerName,
    DateOnly? InvoiceDate,
    DateOnly? OrderDate,
    decimal TotalQuantity,
    DateTime CreatedAtUtc);

public record SalesSummaryResponse(int TotalInvoices, decimal TotalQuantity, decimal AverageQuantityPerInvoice);
public record SalesPointResponse(string Label, decimal Quantity, int InvoiceCount);
public record TopCustomerResponse(string CustomerName, decimal Quantity, int InvoiceCount);
