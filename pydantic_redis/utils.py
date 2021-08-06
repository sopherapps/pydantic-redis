"""Module containing common utilities"""


def bytes_to_string(data: bytes):
    """Converts data to string"""
    return str(data, "utf-8") if isinstance(data, bytes) else data
