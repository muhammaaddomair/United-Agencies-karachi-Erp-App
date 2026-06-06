using Microsoft.EntityFrameworkCore;
using UnitedDrugsApi.Domain;

namespace UnitedDrugsApi.Infrastructure.Persistence;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<User> Users => Set<User>();
    public DbSet<RefreshToken> RefreshTokens => Set<RefreshToken>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<InventoryStock> InventoryStocks => Set<InventoryStock>();
    public DbSet<StockMovement> StockMovements => Set<StockMovement>();
    public DbSet<Invoice> Invoices => Set<Invoice>();
    public DbSet<InvoiceItem> InvoiceItems => Set<InvoiceItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasIndex(x => x.Username).IsUnique();
        });

        modelBuilder.Entity<RefreshToken>(entity =>
        {
            entity.HasOne(x => x.User)
                .WithMany(x => x.RefreshTokens)
                .HasForeignKey(x => x.UserId);
        });

        modelBuilder.Entity<Product>(entity =>
        {
            entity.HasIndex(x => new { x.RegNo, x.BatchNo, x.ProductDescription });
        });

        modelBuilder.Entity<InventoryStock>(entity =>
        {
            entity.HasKey(x => x.ProductId);
            entity.HasOne(x => x.Product)
                .WithOne(x => x.InventoryStock)
                .HasForeignKey<InventoryStock>(x => x.ProductId);
        });

        modelBuilder.Entity<StockMovement>(entity =>
        {
            entity.HasOne(x => x.Product)
                .WithMany(x => x.StockMovements)
                .HasForeignKey(x => x.ProductId);
        });

        modelBuilder.Entity<Invoice>(entity =>
        {
            entity.HasIndex(x => x.BillNo).IsUnique();
        });

        modelBuilder.Entity<InvoiceItem>(entity =>
        {
            entity.HasOne(x => x.Invoice)
                .WithMany(x => x.Items)
                .HasForeignKey(x => x.InvoiceId);

            entity.HasOne(x => x.Product)
                .WithMany()
                .HasForeignKey(x => x.ProductId);
        });
    }
}
