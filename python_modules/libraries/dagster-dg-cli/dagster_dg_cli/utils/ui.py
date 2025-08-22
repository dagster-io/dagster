import itertools
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

from yaspin import Spinner, yaspin
from yaspin.core import Yaspin

# "Daggy" octopus-like unicode characters
DAGGY_SPINNER_FRAMES = "ଳଢଡଜ"
DEFAULT_SPINNER_INTERVAL = 0.1  # seconds between spinner frame updates
DEFAULT_ELLIPSIS_INTERVAL = 0.5  # seconds between ellipsis animation updates


def format_duration(seconds: Optional[float]) -> str:
    """Format duration in a human-readable way."""
    if seconds is None:
        return "0s"
    elif seconds < 60:
        return f"{seconds:.0f}s"
    else:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"


@contextmanager
def daggy_spinner_context(
    message: str,
    *,
    color: str = "magenta",
    spinner_interval: float = DEFAULT_SPINNER_INTERVAL,
    ellipsis_interval: float = DEFAULT_ELLIPSIS_INTERVAL,
) -> Iterator[Yaspin]:
    import typer

    """Create a context manager for a custom animated spinner with dynamic dots.

    This context manager provides a visually appealing spinner that combines:
    - Custom "Daggy" octopus-like unicode character frames for the main spinner animation
    - Dynamic dots that cycle through ".", "..", "...", "" to show progress
    - Configurable color styling and spinner text

    The spinner is designed for long-running operations where users need visual
    feedback that the system is working.

    Args:
        message: The base message to display alongside the spinner
        color: Foreground color for the spinner text. Can be a typer color name
               (e.g., "magenta", "cyan", "green") or any valid color string.
               Defaults to "magenta".
        spinner_interval: Seconds between spinner frame updates. Lower values
                         create faster animation. Defaults to 0.1 seconds.
        ellipsis_interval: Seconds between ellipsis animation updates. Lower values
                          create faster dot cycling. Defaults to 0.5 seconds.

    Yields:
        Yaspin: The spinner instance that can be used to write additional output
    """
    # Create spinner with configurable interval (convert seconds to milliseconds)
    spinner_config = Spinner(frames=DAGGY_SPINNER_FRAMES, interval=int(spinner_interval * 1000))
    stop_thread = threading.Event()

    def update_text():
        """Update the spinner text with cycling dots in a separate thread."""
        dots = itertools.cycle([".", "..", "...", ""])
        while not stop_thread.is_set():
            # Try to get typer color constant, fallback to string if not found
            try:
                color_value = getattr(typer.colors, color.upper())
            except AttributeError:
                color_value = color
            spinner.text = typer.style(f"{message}{next(dots)}", fg=color_value)
            time.sleep(ellipsis_interval)

    with yaspin(spinner_config, text=message, color=color) as spinner:
        # Start the text update thread
        thread = threading.Thread(target=update_text, daemon=True)
        thread.start()

        try:
            yield spinner
        finally:
            # Clean up the thread
            stop_thread.set()
            thread.join()
