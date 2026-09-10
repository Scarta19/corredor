"""Reusable column types shared by the domain models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import JSONB


def pg_enum[E: StrEnum](enum_cls: type[E], name: str) -> SAEnum:
    """A native Postgres enum that stores the StrEnum *values*, not member names."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        values_callable=lambda cls: [member.value for member in cls],
        validate_strings=True,
    )


#: Monetary amounts. Insurance premiums in COP are large but never fractional
#: beyond two places; Numeric keeps them exact where float would not.
Dinero = Numeric(14, 2)

#: Free-form structured payloads (dynamic form answers, model features,
#: provider webhook envelopes). Queried with Postgres JSONB operators.
Json: Any = JSONB
