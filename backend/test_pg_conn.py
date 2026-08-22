import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect("postgresql://phantom_app:phantom_app_secure_password_2026@172.19.222.170:5432/phantom")
        val = await conn.fetchval("SELECT version()")
        print("Connected successfully via 172.19.222.170:", val)
        await conn.close()
    except Exception as e:
        print("Failed to connect via 172.19.222.170:", type(e), e)

if __name__ == "__main__":
    asyncio.run(main())
