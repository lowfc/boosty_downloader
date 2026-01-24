import asyncio
from dataclasses import dataclass
from typing import List


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

    def ready(self) -> bool:
        return not self._done and not self._pending

    @property
    def percent(self) -> float:
        return self._percent / 100

    @property
    def pending(self) -> bool:
        return self._pending

    async def run(self):
        if self._done or self._pending:
            return
        self._pending = True
        async with self._semaphore:
            for i in range(10):
                self._percent += 10
                await asyncio.sleep(0.5)
            self._done = True
            self._pending = False


@dataclass
class TaskInfo:
    percent: int
    title: str
    author: str
    post_id: str
    path: str


class DownloadManager:
    def __init__(self, maximum_concurrency: int = 5):
        self._tasks = {}
        self.maximum_concurrency = maximum_concurrency
        self._semaphore = asyncio.Semaphore(self.maximum_concurrency)
        self._lock = asyncio.Lock()
        self._closed = False

    async def add_task(self, author: str, post_id: str):
        async with self._lock:
            if not post_id in self._tasks.keys():
                self._tasks[post_id] = Task(self._semaphore, post_id=post_id, author=author)

    async def mainloop(self):
        while not self._closed:
            async with self._lock:
                for post_id in self._tasks.keys():
                    if self._tasks[post_id].ready():
                        asyncio.create_task(self._tasks[post_id].run())
            await asyncio.sleep(5)

    async def get_pending_tasks(self) -> int:
        async with self._lock:
            result = 0
            for post_id in self._tasks.keys():
                if self._tasks[post_id].pending:
                    result += 1
            return result

    @property
    def total_tasks(self) -> int:
        return len(self._tasks)

    async def get_tasks(self, limit: int = 10, offset: int = 0) -> List[TaskInfo]:
        result = []
        current_offset = 0
        async with self._lock:
            for n, post_id in enumerate(self._tasks.keys()):
                if current_offset >= offset:
                    result.append(TaskInfo(
                        percent=self._tasks[post_id].percent,
                        title=self._tasks[post_id].title,
                        author=self._tasks[post_id].author,
                        path=self._tasks[post_id].path,
                        post_id=post_id,
                    ))
                    if len(result) == limit:
                        return result
                current_offset += 1
        return result
