import asyncio
from typing import Optional

from core.defs.tasks import TaskError


class Task:
    def __init__(self, semaphore: asyncio.Semaphore, author: str, post_id: str):
        self._semaphore = semaphore
        self.author = author
        self.post_id = post_id
        self.title = None
        self.path = None
        self._percent = 0
        self._done = False
        self._pending = False
        self._error = False
        self._task = None
        self.error_description: Optional[TaskError] = None

    def ready(self) -> bool:
        return not self._done and not self._pending and not self._error

    @property
    def percent(self) -> float:
        return self._percent / 100

    @property
    def pending(self) -> bool:
        return self._pending

    def launch(self):
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        """ Some preflight here """
        self._task.cancel()
        self._task = None
        self._pending = False
        self._error = True
        self.error_description = TaskError.CANCELLED

    async def retry(self):
        if self._done or self._pending:
            return
        """ Some preflight here """
        self._percent = 0
        self._error = False
        self.error_description = None
        self.launch()

    async def _run(self):
        if self._done or self._pending:
            return
        self._pending = True
        async with self._semaphore:
            for i in range(10):
                self._percent += 10
                await asyncio.sleep(0.5)
            self._done = True
            self._pending = False