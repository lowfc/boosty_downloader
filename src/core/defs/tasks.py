from dataclasses import dataclass
from enum import Enum
from typing import Optional

import flet as ft


class TaskError(Enum):
    CANCELLED = "cancelled"
    ERROR = "ERROR"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    ACCESS_DENIED = "ACCESS_DENIED"
    NO_HOME_FOLDER = "NO_HOME_FOLDER"


@dataclass
class TaskInfo:
    percent: float
    title: str
    author: str
    post_id: str
    path: str
    finished: bool
    count_files: int
    total_weight: int
    error: Optional[TaskError] = None


TASK_ERROR_STATUS_LINE = {
    TaskError.CANCELLED: [ft.Icons.KEYBOARD_TAB_ROUNDED, "Cancelled"],
    TaskError.ERROR: [ft.Icons.CANCEL_ROUNDED, "An error has occurred"],
    TaskError.ALREADY_EXISTS: [ft.Icons.REMOVE_RED_EYE_ROUNDED, "Already exists"],
    TaskError.ACCESS_DENIED: [ft.Icons.LOCK_ROUNDED, "Don't have access to post"],
    TaskError.NO_HOME_FOLDER: [ft.Icons.FOLDER_OFF, "Download directory unavailable"],
}
