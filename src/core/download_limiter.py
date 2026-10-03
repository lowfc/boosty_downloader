import asyncio


class DownloadLimiter:
    """Resize download slots without interrupting posts already downloading."""

    def __init__(self, limit: int):
        if limit < 1:
            raise ValueError("Download limit must be positive")
        self.limit = limit
        self.active = 0
        self.condition = asyncio.Condition()

    async def set_limit(self, limit: int):
        if limit < 1:
            raise ValueError("Download limit must be positive")
        async with self.condition:
            self.limit = limit
            self.condition.notify_all()

    async def __aenter__(self):
        async with self.condition:
            await self.condition.wait_for(lambda: self.active < self.limit)
            self.active += 1
        return self

    async def __aexit__(self, *args):
        async with self.condition:
            self.active -= 1
            self.condition.notify_all()
