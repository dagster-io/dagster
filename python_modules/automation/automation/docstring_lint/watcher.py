"""File watching functionality for docstring validation."""

import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class DocstringValidationHandler(FileSystemEventHandler):
    """Handler for file system events that triggers docstring validation."""

    def __init__(
        self, target_file: Path, validation_callback: Callable[[], None], verbose: bool = False
    ) -> None:
        """Initialize the handler.

        Args:
            target_file: The file to watch for changes
            validation_callback: Function to call when the file changes
            verbose: Whether to print debug information about file events
        """
        self.target_file = target_file.resolve()
        self.validation_callback = validation_callback
        self.last_validation_time = 0
        self.debounce_delay = 0.5  # 500ms debounce
        self.verbose = verbose

    def _handle_file_event(self, event_path: Path, event_type: str) -> None:
        """Handle file system events for the target file."""
        if self.verbose:
            print(f"[DEBUG] {event_type} event: {event_path}")  # noqa: T201

        if event_path == self.target_file:
            current_time = time.time()
            if current_time - self.last_validation_time > self.debounce_delay:
                self.last_validation_time = current_time
                if self.verbose:
                    print(f"[DEBUG] Triggering validation for {event_path}")  # noqa: T201
                self.validation_callback()
            elif self.verbose:
                print("[DEBUG] Skipping validation (debounced)")  # noqa: T201

    def on_modified(self, event) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return
        self._handle_file_event(Path(str(event.src_path)).resolve(), "MODIFIED")

    def on_moved(self, event) -> None:
        """Handle file move events (common with atomic saves)."""
        if event.is_directory:
            return
        # Check if the destination is our target file (atomic save pattern)
        self._handle_file_event(Path(str(event.dest_path)).resolve(), "MOVED")

    def on_created(self, event) -> None:
        """Handle file creation events (some editors recreate files)."""
        if event.is_directory:
            return
        self._handle_file_event(Path(str(event.src_path)).resolve(), "CREATED")


class DocstringFileWatcher:
    """Watches a file for changes and triggers docstring validation."""

    def __init__(
        self, target_file: Path, validation_callback: Callable[[], None], verbose: bool = False
    ) -> None:
        """Initialize the file watcher.

        Args:
            target_file: The file to watch for changes
            validation_callback: Function to call when the file changes
            verbose: Whether to print debug information about file events
        """
        self.target_file = target_file.resolve()
        self.validation_callback = validation_callback
        self.observer = Observer()
        self.handler = DocstringValidationHandler(target_file, validation_callback, verbose)

    def start_watching(self) -> None:
        """Start watching the file for changes."""
        if not self.target_file.exists():
            raise FileNotFoundError(f"Target file does not exist: {self.target_file}")

        # Watch the parent directory since we need to catch modifications to the file
        watch_dir = self.target_file.parent
        self.observer.schedule(self.handler, str(watch_dir), recursive=False)
        self.observer.start()

    def stop_watching(self) -> None:
        """Stop watching the file for changes."""
        self.observer.stop()
        self.observer.join()
