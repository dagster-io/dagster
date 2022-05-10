import socket
import struct
from urllib.parse import urlparse

import dagster._check as check


def is_loopback(host):
    addr_info = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)[0]
    sockaddr = addr_info[4][0]
    return struct.unpack("!I", socket.inet_aton(sockaddr))[0] >> (32 - 8) == 127


def is_local_uri(address):
    """Determine if an address (full URI, DNS or IP) is local.

    Args:
        address (str): The URI or IP address to evaluate

    Returns:
        bool: Whether the address appears to represent a local interface.
    """
    check.str_param(address, "address")

    # Handle the simple cases with no protocol specified. Per
    # https://docs.python.org/3/library/urllib.parse.html, urlparse recognizes a netloc only if it
    # is properly introduced by '//' (e.g. has a scheme specified).
    hostname = urlparse(address).hostname if "//" in address else address.split(":")[0]

    # Empty protocol only specified as URI, e.g. "rpc://"
    if hostname is None:
        return True

    # Get the IPv4 address from the hostname. Returns a triple (hostname, aliaslist, ipaddrlist), so
    # we grab the 0th element of ipaddrlist.
    try:
        ip_addr_str = socket.gethostbyname_ex(hostname)[-1][0]
    except socket.gaierror:
        # Invalid hostname, so assume not local host
        return False

    # Special case this since it isn't technically loopback
    if ip_addr_str == "0.0.0.0":
        return True

    return is_loopback(ip_addr_str)
