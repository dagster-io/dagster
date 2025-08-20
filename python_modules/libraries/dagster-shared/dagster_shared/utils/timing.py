def format_duration(milliseconds: float) -> str:
    """Given milliseconds, return human readable duration string such as:
    533ms, 2.1s, 4m52s, 34m12s, 1h4m.
    """
    # under 1 ms
    # ex: 0.83ms
    # ex: 8.3ms
    if milliseconds < 10:
        return f"{round(milliseconds, 2)}ms"

    # between 10 ms and 1000 ms
    # ex: 533ms
    if milliseconds < 1000:
        return f"{int(milliseconds)}ms"

    # between one second and one minute
    # ex: 5.6s
    if milliseconds < 1000 * 60:
        seconds = milliseconds / 1000
        return f"{round(seconds, 2)}s"

    # between one minute and 60 minutes
    # 5m42s
    if milliseconds < 1000 * 60 * 60:
        minutes = int(milliseconds // (1000 * 60))
        seconds = int(milliseconds % (1000 * 60) // (1000))
        return f"{minutes}m{seconds}s"

    # Above one hour
    else:
        hours = int(milliseconds // (1000 * 60 * 60))
        minutes = int(milliseconds % (1000 * 60 * 60) // (1000 * 60))
        return f"{hours}h{minutes}m"
