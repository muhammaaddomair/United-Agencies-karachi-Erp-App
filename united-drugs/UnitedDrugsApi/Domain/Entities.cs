using System.ComponentModel.DataAnnotations;

namespace UnitedDrugsApi.Domain;

public class User
{
    public Guid Id { get; set; } = Guid.NewGuid();
    [MaxLength(100)] public string Username { get; set; } = string.Empty;
    [MaxLength(255)] public string PasswordHash { get; set; } = string.Empty;
    [MaxLength(30)] public string Role { get; set; } = "user";
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAtUtc { get; set; } = DateTime.UtcNow;
    public ICollection<RefreshToken> RefreshTokens { get; set; } = new List<RefreshToken>();
}

public class RefreshToken
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid UserId { get; set; }
    public User User { get; set; } = null!;
    [MaxLength(255)] public string TokenHash { get; set; } = string.Empty;
    public DateTime ExpiresAtUtc { get; set; }
    public DateTime? RevokedAtUtc { get; set; }
    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
}

public class Product
{
    public Guid Id { get; set; } = Guid.NewGuid();
    [MaxLength(100)] public string RegNo { get; set; } = string.Empty;
    [MaxLength(100)] public string BatchNo { get; set; } = string.Empty;
    public DateOnly? MfgDate { get; set; }
    public DateOnly? ExpDate { get; set; }
    [MaxLength(500)] public string ProductDescription { get; set; } = string.Empty;
    public decimal TradePrice { get; set; }
    public decimal DiscountPercent { get; set; }
    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAtUtc { get; set; } = DateTime.UtcNow;
    public InventoryStock? InventoryStock { get; set; }
    public ICollection<StockMovement> StockMovements { get; set; } = new List<StockMovement>();
}

public class InventoryStock
{
    public Guid ProductId { get; set; }
    public Product Product { get; set; } = null!;
    public decimal QuantityOnHand { get; set; }
    public DateTime UpdatedAtUtc { get; set; } = DateTime.UtcNow;
}

public class StockMovement
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid ProductId { get; set; }
    public Product Product { get; set; } = null!;
    [MaxLength(30)] public string MovementType { get; set; } = string.Empty;
    public decimal Quantity { get; set; }
    [MaxLength(50)] public string ReferenceType { get; set; } = string.Empty;
    [MaxLength(100)] public string ReferenceId { get; set; } = string.Empty;
    [MaxLength(500)] public string Notes { get; set; } = string.Empty;
    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
    public Guid? CreatedByUserId { get; set; }
}

public class Invoice
{
    public Guid Id { get; set; } = Guid.NewGuid();
    [MaxLength(100)] public string InvoiceNo { get; set; } = string.Empty;
    [MaxLength(100)] public string BillNo { get; set; } = string.Empty;
    [MaxLength(255)] public string CustomerName { get; set; } = string.Empty;
    public string ToText { get; set; } = string.Empty;
    [MaxLength(100)] public string StrNo { get; set; } = string.Empty;
    [MaxLength(100)] public string NtnNo { get; set; } = string.Empty;
    [MaxLength(100)] public string DeliveryChallanNo { get; set; } = string.Empty;
    [MaxLength(150)] public string OrderContractNo { get; set; } = string.Empty;
    public DateOnly? OrderDate { get; set; }
    [MaxLength(150)] public string InspectionNoteNo { get; set; } = string.Empty;
    public DateOnly? InvoiceDate { get; set; }
    public decimal TotalQuantity { get; set; }
    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
    public Guid? CreatedByUserId { get; set; }
    public ICollection<InvoiceItem> Items { get; set; } = new List<InvoiceItem>();
}

public class InvoiceItem
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid InvoiceId { get; set; }
    public Invoice Invoice { get; set; } = null!;
    public Guid ProductId { get; set; }
    public Product Product { get; set; } = null!;
    [MaxLength(500)] public string ProductDescription { get; set; } = string.Empty;
    public decimal Quantity { get; set; }
    public decimal UnitPrice { get; set; }
}
