using Microsoft.EntityFrameworkCore;
using UnitedDrugsApi.Domain;
using UnitedDrugsApi.Infrastructure.Auth;

namespace UnitedDrugsApi.Infrastructure.Persistence;

public static class DatabaseSeeder
{
    public static async Task SeedAsync(AppDbContext dbContext, IPasswordHasher passwordHasher)
    {
        await dbContext.Database.MigrateAsync();

        if (!await dbContext.Users.AnyAsync(x => x.Username == "admin"))
        {
            dbContext.Users.Add(new User
            {
                Username = "admin",
                PasswordHash = passwordHasher.Hash("myadmin786"),
                Role = "admin",
            });
        }

        if (!await dbContext.Users.AnyAsync(x => x.Username == "user"))
        {
            dbContext.Users.Add(new User
            {
                Username = "user",
                PasswordHash = passwordHasher.Hash("user123"),
                Role = "user",
            });
        }

        await dbContext.SaveChangesAsync();
    }
}
