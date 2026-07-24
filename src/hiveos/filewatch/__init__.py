"""File Watch Folder — customer drop folders with auto-ingest."""

from .models import (
    WatchFolder,
    WatchFolderStatus,
    FileEvent,
    FileEventKind,
    generate_folder_id,
)
from .service import FileWatchService

__all__ = [
    "WatchFolder",
    "WatchFolderStatus",
    "FileEvent",
    "FileEventKind",
    "FileWatchService",
    "generate_folder_id",
]
