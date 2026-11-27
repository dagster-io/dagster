"""Reads OpenSSH known_hosts files the way OpenSSH matches them."""

import base64
import hashlib
import hmac
import re
from collections.abc import Iterable

import paramiko
from dagster_shared.record import record
from paramiko.hostkeys import HostKeyEntry, InvalidHostKey
from paramiko.pkey import PKey


@record
class KnownHostKeys:
    known: list[PKey]
    revoked: list[PKey]


def known_keys(known_hosts_files: Iterable[str], hostname: str) -> KnownHostKeys:
    """The keys known_hosts lists for ``hostname``, and the keys marked ``@revoked`` for it.

    - ``known`` leaves out revoked keys, and keeps several keys of one type.
    - Entries match the way OpenSSH matches them: case-insensitively, with ``*``, ``?`` and ``!``.
    - Unparseable lines and ``@cert-authority`` lines are skipped: host certificates are not
      supported.
    """
    keys, revoked = [], []
    for path in known_hosts_files:
        # Comments may be in any encoding; host names and keys are ASCII.
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                marker = None
                if line.startswith("@"):
                    marker, *rest = line.split(None, 1)
                    line = rest[0] if rest else ""
                entry = parse_known_hosts_line(line)
                if entry is None or not matches_host(entry.hostnames, hostname):
                    continue
                if marker is None:
                    keys.append(entry.key)
                elif marker == "@revoked":
                    revoked.append(entry.key)
    revoked_blobs = {key.asbytes() for key in revoked}
    return KnownHostKeys(
        known=[key for key in keys if key.asbytes() not in revoked_blobs], revoked=revoked
    )


def parse_known_hosts_line(line: str) -> HostKeyEntry | None:
    # Key classes raise ValueError for a malformed key blob, such as a short Ed25519 key.
    try:
        return HostKeyEntry.from_line(line)
    except (paramiko.SSHException, InvalidHostKey, ValueError):
        return None


def matches_host(patterns: Iterable[str], host: str) -> bool:
    """Whether an entry's comma-separated patterns match ``host``; a negated match excludes it."""
    matched = False
    for pattern in patterns:
        if matches_pattern(pattern.removeprefix("!"), host):
            if pattern.startswith("!"):
                return False
            matched = True
    return matched


def matches_pattern(pattern: str, host: str) -> bool:
    if pattern.startswith("|1|"):
        # OpenSSH hashes the lowercased name, and paramiko hashes the name as given.
        return any(matches_hashed_name(pattern, name) for name in (host, host.lower()))
    regex = "".join(
        ".*" if char == "*" else "." if char == "?" else re.escape(char) for char in pattern.lower()
    )
    return re.fullmatch(regex, host.lower()) is not None


def matches_hashed_name(hashed_name: str, host: str) -> bool:
    """Matches an OpenSSH ``|1|salt|hmac`` name; a malformed one matches nothing."""
    parts = hashed_name.split("|")
    if len(parts) != 4:
        return False
    try:
        salt = base64.b64decode(parts[2], validate=True)
        digest = base64.b64decode(parts[3], validate=True)
    except ValueError:
        return False
    expected = hmac.new(salt, host.encode(), hashlib.sha1).digest()
    return len(salt) == hashlib.sha1().digest_size and hmac.compare_digest(expected, digest)
