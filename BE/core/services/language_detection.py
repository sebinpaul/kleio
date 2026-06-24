import logging
import re

from langdetect import LangDetectException, detect

logger = logging.getLogger(__name__)

MIN_DETECT_LENGTH = 20

_WHITESPACE = re.compile(r"\s+")


def detect_language(text: str) -> str:
    """
    Detect ISO 639-1 language code from text.
    Returns empty string when text is too short or detection fails.
    """
    cleaned = _WHITESPACE.sub(" ", (text or "").strip())
    if len(cleaned) < MIN_DETECT_LENGTH:
        return ""

    try:
        code = detect(cleaned)
        return (code or "").strip().lower()[:2]
    except LangDetectException:
        logger.debug("Language detection failed for text snippet: %r", cleaned[:80])
        return ""
    except Exception:
        logger.exception("Unexpected language detection error")
        return ""
