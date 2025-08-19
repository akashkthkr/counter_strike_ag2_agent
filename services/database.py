import os
from typing import AsyncGenerator
import asyncpg
from contextlib import asynccontextmanager


class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://cs_user:cs_password@localhost:5432/counter_strike_db")
        self.pool = None

    async def initialize(self):
        self.pool = await asyncpg.create_pool(self.database_url, min_size=5, max_size=20)

    async def close(self):
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            yield connection


db_manager = DatabaseManager()
