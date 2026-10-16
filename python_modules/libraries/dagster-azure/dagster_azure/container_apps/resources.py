_KIB = 1024
_MIB = _KIB**2
_GIB = _KIB**3


def interpret_aca_mem_str_as_bytes(mem_str: str | None) -> int | None:
    """Parse an ACA-style memory string (e.g. "0.5Gi", "512Mi") as bytes.

    Returns None if input is None. Raises ValueError on unrecognized suffixes
    or non-numeric values.
    """
    if mem_str is None:
        return None

    s = mem_str.strip()
    for suffix, multiplier in (("Gi", _GIB), ("Mi", _MIB), ("Ki", _KIB)):
        if s.endswith(suffix):
            return int(float(s[: -len(suffix)]) * multiplier)

    # Bare number = bytes
    return int(float(s))


def interpret_aca_cpu_str_as_millicpus(cpu_str: str | None) -> int | None:
    """Parse an ACA-style CPU string as millicpus.

    Accepts decimal cores ("0.5", "1", "1.0") or the m-suffix ("500m", "1000m").
    Returns None if input is None. Raises ValueError on non-numeric values.
    """
    if cpu_str is None:
        return None

    s = cpu_str.strip()
    if s.endswith("m"):
        return int(float(s[:-1]))
    return int(float(s) * 1000)
