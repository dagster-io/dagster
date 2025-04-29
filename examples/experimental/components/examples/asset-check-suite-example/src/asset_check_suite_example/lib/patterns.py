from typing import Literal

PatternType = Literal[
    "email",
    "uuid",
    "zip_code",
    "us_state_code",
    "us_phone_number",
    "us_ssn",
    "credit_card",
    "ipv4",
    "ipv6",
    "mac_address",
    "iso_date",
    "iso_datetime",
    "hex_color",
]

REGEX_PATTERNS = {
    # Email validation
    # This covers most common email formats with alphanumeric characters, dots, underscores, and hyphens
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    # UUID (Universal Unique Identifier) - version 4 format
    # Format: 8-4-4-4-12 hexadecimal characters (36 chars including hyphens)
    "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    # US ZIP Code (5 digits with optional 4-digit extension)
    "zip_code": r"^\d{5}(?:-\d{4})?$",
    # US State Code (2 uppercase letters)
    "us_state_code": r"^[A-Z]{2}$",
    # US Phone Number (multiple formats)
    # Formats: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
    "us_phone_number": r"^(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$",
    # US Social Security Number (SSN)
    # Format: 123-45-6789 or 123456789
    "us_ssn": r"^(?:\d{3}-\d{2}-\d{4}|\d{9})$",
    # Credit Card Number (major cards)
    # Validates formats for Visa, MasterCard, American Express, Discover, etc.
    "credit_card": r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})$",
    # IPv4 Address
    "ipv4": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
    # IPv6 Address (simplified)
    "ipv6": r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}$|^[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}$|^[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,4}[0-9a-fA-F]{1,4}$|^(?:[0-9a-fA-F]{1,4}:){0,2}[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,3}[0-9a-fA-F]{1,4}$|^(?:[0-9a-fA-F]{1,4}:){0,3}[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,2}[0-9a-fA-F]{1,4}$|^(?:[0-9a-fA-F]{1,4}:){0,4}[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:)?[0-9a-fA-F]{1,4}$|^(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}::[0-9a-fA-F]{1,4}$|^(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}::$",
    # MAC Address (multiple formats)
    # Formats: 01:23:45:67:89:AB, 01-23-45-67-89-AB, 0123.4567.89AB
    "mac_address": r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$",
    # ISO Date (YYYY-MM-DD)
    "iso_date": r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])$",
    # ISO DateTime (YYYY-MM-DDThh:mm:ss.sssZ or YYYY-MM-DDThh:mm:ss.sss+hh:mm)
    "iso_datetime": r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.\d+)?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])$",
    # Hex Color Code (#RGB or #RRGGBB)
    "hex_color": r"^#(?:[0-9a-fA-F]{3}){1,2}$",
}
