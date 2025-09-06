import re
from . import __name__ as _utils_pkg
from ..core.logging import logger


STOP_PT = {
    "de", "da", "do", "dos", "das", "o", "a", "os", "as", "um", "uma", "para", "por",
    "em", "e", "ou", "que", "com", "no", "na", "nos", "nas"
}
STOP_EN = {
    "the", "a", "an", "in", "on", "at", "of", "for", "and", "or", "to", "is", "are",
    "be", "was", "were", "this", "that"
}
STOP = STOP_PT | STOP_EN


def preprocess(text: str) -> str:
    logger.debug(f"Preprocess in chars={len(text) if text else 0}")

    text = re.sub(r"\s+", " ", (text or "")).strip()
    tokens = re.findall(r"\b\w+\b", text.lower())
    kept = [t for t in tokens if t not in STOP]
    out = " ".join(kept) if kept else text
    logger.debug(f"Preprocess out chars={len(out)}")

    return out

