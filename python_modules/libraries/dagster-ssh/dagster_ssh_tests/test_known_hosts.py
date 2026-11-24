import base64
from pathlib import Path

import paramiko
import pytest
from dagster_ssh.known_hosts import known_keys
from paramiko.message import Message

KEY = paramiko.ECDSAKey.generate()
OTHER_KEY = paramiko.ECDSAKey.generate()


def line(names: str, key: paramiko.PKey, marker: str = "") -> str:
    return f"{marker}{names} {key.get_name()} {key.get_base64()}"


def raw_line(names: str, key_type: str, *fields: bytes) -> str:
    """A known_hosts line whose key blob holds ``fields`` as SSH strings, valid or not."""
    message = Message()
    message.add_string(key_type.encode())
    for field in fields:
        message.add_string(field)
    return f"{names} {key_type} {base64.b64encode(message.asbytes()).decode()}"


@pytest.mark.parametrize(
    "lines, hostname, expected",
    [
        pytest.param([line("gw.example.com", KEY)], "gw.example.com", [KEY], id="exact"),
        pytest.param([line("gw.example.com", KEY)], "other.example.com", [], id="other_host"),
        pytest.param(
            [line("GW.Example.com", KEY)], "gw.example.com", [KEY], id="listed_in_other_case"
        ),
        pytest.param(
            [line("gw.example.com", KEY)], "GW.Example.com", [KEY], id="looked_up_in_other_case"
        ),
        pytest.param([line("*.example.com", KEY)], "gw.example.com", [KEY], id="wildcard"),
        pytest.param(
            [line("gw?.example.com", KEY)],
            "gw1.example.com",
            [KEY],
            id="single_character_wildcard",
        ),
        pytest.param(
            [line("*.example.com,!gw.example.com", KEY)], "gw.example.com", [], id="negated"
        ),
        pytest.param(
            [line("[*.example.com]:2222", KEY)],
            "[gw.example.com]:2222",
            [KEY],
            id="wildcard_with_port",
        ),
        pytest.param(
            [line("[*.example.com]:2222", KEY)],
            "gw.example.com",
            [],
            id="port_entry_for_default_port",
        ),
        pytest.param(
            [line(paramiko.HostKeys.hash_host("gw.example.com"), KEY)],
            "gw.example.com",
            [KEY],
            id="hashed",
        ),
        pytest.param(
            [line(paramiko.HostKeys.hash_host("GW.Example.com"), KEY)],
            "GW.Example.com",
            [KEY],
            id="hashed_from_mixed_case_name",
        ),
        pytest.param(
            [line(paramiko.HostKeys.hash_host("gw.example.com"), KEY)],
            "GW.Example.com",
            [KEY],
            id="hashed_from_lowercased_name",
        ),
        pytest.param(
            [line("|1|truncated|line", OTHER_KEY), line("gw.example.com", KEY)],
            "gw.example.com",
            [KEY],
            id="corrupt_hashed_line",
        ),
        pytest.param(
            [line("|1|\u00e9|\u00e9", OTHER_KEY), line("gw.example.com", KEY)],
            "gw.example.com",
            [KEY],
            id="non_ascii_hashed_line",
        ),
        pytest.param(
            [raw_line("gw.example.com", "ssh-ed25519", b"short"), line("gw.example.com", KEY)],
            "gw.example.com",
            [KEY],
            id="corrupt_ed25519_key",
        ),
        pytest.param(
            [raw_line("gw.example.com", "ssh-rsa", b"\x00", b"\x00"), line("gw.example.com", KEY)],
            "gw.example.com",
            [KEY],
            id="corrupt_rsa_key",
        ),
        pytest.param(
            [line("gw.example.com", KEY), line("gw.example.com", OTHER_KEY)],
            "gw.example.com",
            [KEY, OTHER_KEY],
            id="several_keys_of_one_type",
        ),
        pytest.param(
            [line("gw.example.com", KEY), line("gw.example.com", KEY, "@revoked ")],
            "gw.example.com",
            [],
            id="revoked",
        ),
        pytest.param(
            [line("gw.example.com", KEY), line("gw.example.com", KEY, "@revoked\t")],
            "gw.example.com",
            [],
            id="revoked_after_tab",
        ),
        pytest.param(
            [line("gw.example.com", KEY), "@revoked"],
            "gw.example.com",
            [KEY],
            id="marker_without_entry",
        ),
        pytest.param(
            [line("gw.example.com", KEY), line("*", OTHER_KEY, "@cert-authority ")],
            "gw.example.com",
            [KEY],
            id="cert_authority_line",
        ),
    ],
)
def test_known_keys(tmp_path: Path, lines: list[str], hostname: str, expected: list) -> None:
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text("\n".join(lines) + "\n", encoding="utf-8")

    keys = known_keys([str(known_hosts)], hostname).known

    assert [key.asbytes() for key in keys] == [key.asbytes() for key in expected]


def test_known_keys_reads_files_with_non_utf8_comments(tmp_path: Path) -> None:
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_bytes(
        "# hôtes de confiance\n".encode("latin-1") + (line("gw.example.com", KEY) + "\n").encode()
    )

    keys = known_keys([str(known_hosts)], "gw.example.com").known

    assert [key.asbytes() for key in keys] == [KEY.asbytes()]


def test_known_keys_lists_revoked_keys_for_the_host(tmp_path: Path) -> None:
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text(
        line("gw.example.com", KEY)
        + "\n"
        + line("*", KEY, "@revoked ")
        + "\n"
        + line("other.example.com", OTHER_KEY, "@revoked ")
        + "\n",
        encoding="utf-8",
    )

    keys = known_keys([str(known_hosts)], "gw.example.com")

    assert keys.known == []
    assert [key.asbytes() for key in keys.revoked] == [KEY.asbytes()]
