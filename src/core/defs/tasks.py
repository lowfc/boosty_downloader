from dataclasses import dataclass
from enum import Enum
from typing import Optional

import flet as ft


class TaskError(Enum):
    CANCELLED = "cancelled"
    ERROR = "ERROR"
    ALREADY_EXISTS = "ALREADY_EXISTS"


@dataclass
class TaskInfo:
    percent: int
    title: str
    author: str
    post_id: str
    path: str
    closed: bool
    error: Optional[TaskError] = None


TASK_ERROR_STATUS_LINE = {
    TaskError.CANCELLED: [ft.Icons.KEYBOARD_TAB_ROUNDED, "Cancelled"],
    TaskError.ERROR: [ft.Icons.CANCEL_ROUNDED, "An error has occurred"],
    TaskError.ALREADY_EXISTS: [ft.Icons.REMOVE_RED_EYE_ROUNDED, "Already exists"],
}