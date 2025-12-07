import random
import string

import inflect

_engine = inflect.engine()


def pluralize_word(count: int, word: str, *, show_count: bool = False) -> str:
    """
    Return singular or plural form of ``word`` based on ``count``.

    If ``show_count=True``, prefixes the number (e.g. "5 cats").
    """
    result = word if count == 1 else _engine.plural(word)
    return f"{count} {result}" if show_count else result


def clean_string(s: str | None) -> str:
    """Return stripped string, turning None/empty into empty string."""
    return (s or "").strip()


def is_str_valued(s: str | None) -> bool:
    """True if ``s`` is non-None and has non-whitespace characters."""
    return bool(s and s.strip())


def random_string(length: int = 8, *, digits: bool = False) -> str:
    """
    Generate a random string of ASCII letters (and optionally digits).

    Useful for temporary names, test data, etc.
    """
    alphabet = string.ascii_letters
    if digits:
        alphabet += string.digits
    return "".join(random.choices(alphabet, k=length))
