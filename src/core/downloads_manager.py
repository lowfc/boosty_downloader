import asyncio
from typing import List, Optional

from core.boosty.defs import BoostyPostDto
from core.defs.tasks import TaskInfo
from core.task import Task


class DownloadManager:
    def __init__(self, maximum_concurrency: int = 5):
        self._tasks = {}
        self.maximum_concurrency = maximum_concurrency
        self._semaphore = asyncio.Semaphore(self.maximum_concurrency)
        self._lock = asyncio.Lock()
        self._closed = False

    async def add_task(self, author: str, post_id: str, post_info: Optional[BoostyPostDto] = None):
        async with self._lock:
            if not post_id in self._tasks.keys():
                self._tasks[post_id] = Task(self._semaphore, post_id=post_id, author=author, post_info=post_info)

    async def mainloop(self):
        while not self._closed:
            async with self._lock:
                for post_id in self._tasks.keys():
                    if self._tasks[post_id].ready():
                        self._tasks[post_id].launch()
            await asyncio.sleep(5)

    async def get_pending_tasks_count(self) -> int:
        async with self._lock:
            result = 0
            for post_id in self._tasks.keys():
                if self._tasks[post_id].pending:
                    result += 1
            return result

    async def get_active_tasks_count(self) -> int:
        async with self._lock:
            result = 0
            for post_id in self._tasks.keys():
                if not self._tasks[post_id].finished:
                    result += 1
            return result

    @property
    def total_tasks(self) -> int:
        return len(self._tasks)

    async def get_tasks(self, limit: int = 10, offset: int = 0, reverse: bool = False) -> List[TaskInfo]:
        result = []
        current_offset = 0
        async with self._lock:
            if reverse:
                task_keys = tuple(reversed(self._tasks.keys()))
            else:
                task_keys = tuple(self._tasks.keys())
            for i in range(len(task_keys)):
                if current_offset >= offset:
                    post_id = task_keys[i]
                    result.append(TaskInfo(
                        percent=self._tasks[post_id].percent,
                        title=self._tasks[post_id].title,
                        author=self._tasks[post_id].author,
                        path=self._tasks[post_id].path,
                        post_id=post_id,
                        finished=self._tasks[post_id].finished,
                        error=self._tasks[post_id].error_description,
                        count_files=self._tasks[post_id].count_files,
                        total_weight=self._tasks[post_id].total_weight,
                    ))
                    if len(result) == limit:
                        return result
                current_offset += 1
        return result

    async def stop_task(self, post_id: str):
        if post_id in self._tasks.keys():
            await self._tasks[post_id].stop()

    async def stop_running_tasks(self):
        for post_id in self._tasks.keys():
            if self._tasks[post_id].pending:
                await self._tasks[post_id].stop()

    async def retry_task(self, post_id: str):
        if post_id in self._tasks.keys():
            await self._tasks[post_id].retry()