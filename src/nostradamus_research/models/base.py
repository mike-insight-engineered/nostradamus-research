"""Common pydantic base configuration."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Forbid unknown fields (catches typos) and never alter string content.

    ``str_strip_whitespace`` is deliberately left off: diplomatic transcriptions
    must be stored byte-for-byte, including leading/trailing whitespace.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=False,
        str_strip_whitespace=False,
    )


SYNTHETIC_PREFIX = "SYN-"
