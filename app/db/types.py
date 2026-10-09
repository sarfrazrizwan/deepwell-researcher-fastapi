from enum import Enum

from sqlalchemy import Enum as SAEnum


def pg_enum(python_enum: type[Enum], name: str) -> SAEnum:
    return SAEnum(
        python_enum,
        name=name,
        native_enum=True,
        values_callable=lambda e: [member.value for member in e],
    )
