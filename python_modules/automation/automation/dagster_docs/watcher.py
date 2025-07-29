"""File watching functionality for docstring validation."""

import time
from pathlib import Path
from typing import Callable

import click
import pathspec
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from automation.dagster_docs.changed_validator import (
    ValidationConfig,
    extract_symbols_from_file,
    print_validation_results,
    validate_symbols,
)
from automation.dagster_docs.file_discovery import git_changed_files


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
            click.echo(f"[DEBUG] {event_type} event: {event_path}")

        if event_path == self.target_file:
            current_time = time.time()
            if current_time - self.last_validation_time > self.debounce_delay:
                self.last_validation_time = current_time
                if self.verbose:
                    click.echo(f"[DEBUG] Triggering validation for {event_path}")
                self.validation_callback()
            elif self.verbose:
                click.echo("[DEBUG] Skipping validation (debounced)")

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


class GitignoreAwareHandler(FileSystemEventHandler):
    """File handler that respects .gitignore patterns."""

    def __init__(self, root_path: Path, parent_watcher: "ChangedFilesWatcher"):
        self.root_path = root_path
        self.parent_watcher = parent_watcher
        self.gitignore_spec = self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> pathspec.PathSpec:
        """Load .gitignore patterns using pathspec library."""
        gitignore_path = self.root_path / ".gitignore"
        if not gitignore_path.exists():
            return pathspec.PathSpec.from_lines("gitwildmatch", [])

        with open(gitignore_path) as f:
            return pathspec.PathSpec.from_lines("gitwildmatch", f.readlines())

    def _should_ignore_path(self, file_path: Path) -> bool:
        """Check if path should be ignored based on .gitignore."""
        # Get relative path from repo root
        try:
            rel_path = file_path.relative_to(self.root_path)
            return self.gitignore_spec.match_file(str(rel_path))
        except ValueError:
            return True  # Outside repo, ignore

    def on_modified(self, event) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))

        # Only watch .py files that aren't gitignored
        if file_path.suffix == ".py" and not self._should_ignore_path(file_path):
            self.parent_watcher._on_file_changed(file_path)  # noqa: SLF001

    def on_moved(self, event) -> None:
        """Handle file move events (common with atomic saves)."""
        if event.is_directory:
            return
        # Check if the destination is a .py file and not gitignored
        dest_path = Path(str(event.dest_path))
        if dest_path.suffix == ".py" and not self._should_ignore_path(dest_path):
            self.parent_watcher._on_file_changed(dest_path)  # noqa: SLF001

    def on_created(self, event) -> None:
        """Handle file creation events (some editors recreate files)."""
        if event.is_directory:
            return
        file_path = Path(str(event.src_path))
        if file_path.suffix == ".py" and not self._should_ignore_path(file_path):
            self.parent_watcher._on_file_changed(file_path)  # noqa: SLF001


class ChangedFilesWatcher:
    """Watches for file changes and dynamically manages docstring validation."""

    def __init__(self, root_path: Path, config: ValidationConfig, verbose: bool = False):
        """Initialize the changed files watcher.

        Args:
            root_path: Root path of the git repository
            config: Validation configuration
            verbose: Whether to print debug information
        """
        self.root_path = root_path
        self.config = config
        self.verbose = verbose
        self.current_changed_files: set[Path] = set()
        self.file_watchers: dict[Path, DocstringFileWatcher] = {}
        self.observer = Observer()
        self.git_refresh_debounce = 1.0  # Debounce git checks
        self.last_git_check = 0

    def _on_file_changed(self, file_path: Path) -> None:
        """Called when any .py file changes - triggers git refresh and watcher updates."""
        # Debounced git status refresh to update the watcher set
        current_time = time.time()
        if current_time - self.last_git_check > self.git_refresh_debounce:
            self.last_git_check = current_time
            self._refresh_git_status()

    def _refresh_git_status(self) -> None:
        """Check git status and update active watchers."""
        new_changed_files = set(git_changed_files(self.root_path))

        # Remove watchers for files no longer changed
        for file_path in self.current_changed_files - new_changed_files:
            if file_path in self.file_watchers:
                self.file_watchers[file_path].stop_watching()
                del self.file_watchers[file_path]
                if self.verbose:
                    click.echo(f"[DEBUG] Stopped watching {file_path} (no longer changed)")

        # Add watchers for newly changed files
        for file_path in new_changed_files - self.current_changed_files:
            callback = self._create_validation_callback(file_path)
            self.file_watchers[file_path] = DocstringFileWatcher(file_path, callback, self.verbose)
            self.file_watchers[file_path].start_watching()
            if self.verbose:
                click.echo(f"[DEBUG] Started watching {file_path} (newly changed)")

        # Update status message if the set changed
        if new_changed_files != self.current_changed_files:
            file_count = len(new_changed_files)
            if file_count == 0:
                click.echo("No changed files to watch")
            else:
                file_names = [f.name for f in new_changed_files]
                click.echo(f"Watching {file_count} changed files: {', '.join(file_names)}")

        self.current_changed_files = new_changed_files

    def _create_validation_callback(self, file_path: Path) -> Callable[[], None]:
        """Create validation callback for a specific changed file."""

        def validate_file() -> None:
            timestamp = time.strftime("%H:%M:%S")
            click.echo(f"[{timestamp}] File changed, validating symbols in {file_path.name}...")

            try:
                # Get module path for this file
                module_path = self.config.path_converter(file_path, self.config.root_path)
                if module_path is None:
                    click.echo(f"Could not determine module path for {file_path}")
                    return

                # Extract and validate symbols from this file
                symbols = extract_symbols_from_file(file_path, module_path)
                if not symbols:
                    click.echo("No symbols found to validate")
                    return

                results = validate_symbols(symbols)
                error_count, warning_count = print_validation_results(results, self.verbose)

                if error_count == 0 and warning_count == 0:
                    click.echo("✓ All docstrings are valid!")
                elif error_count == 0:
                    click.echo(f"✓ All docstrings are valid (with {warning_count} warnings)")
                else:
                    click.echo(f"✗ Found {error_count} errors, {warning_count} warnings")

            except Exception as e:
                click.echo(f"Validation error: {e}", err=True)
                if self.verbose:
                    import traceback

                    traceback.print_exc()

            click.echo("-" * 50)

        return validate_file

    def start_watching(self) -> None:
        """Start watching for file changes, respecting .gitignore."""
        handler = GitignoreAwareHandler(self.root_path, self)
        self.observer.schedule(handler, str(self.root_path), recursive=True)
        self.observer.start()

        # Initial git status check
        self._refresh_git_status()

    def stop_watching(self) -> None:
        """Stop watching for file changes."""
        # Stop all individual file watchers
        for watcher in self.file_watchers.values():
            watcher.stop_watching()
        self.file_watchers.clear()

        # Stop the main observer
        self.observer.stop()
        self.observer.join()


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
