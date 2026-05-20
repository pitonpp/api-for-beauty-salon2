"""Кастомные Pydantic-типы с валидацией (телефон, пароль, цена и т.д.)."""

import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import AfterValidator, Field

from app.constants import (
    DESCRIPTION_PATTERN,
    FIRST_AND_LAST_NAME_PATTERN,
    NAME_PATTERN,
    PASSWORD_PATTERN,
    PHONE_PATTERN,
    USERNAME_PATTERN,
)

PASSWORD_PATTERN_RE = re.compile(PASSWORD_PATTERN)

NAME_PATTERN_RE = re.compile(NAME_PATTERN)


def validate_price(value: Decimal | float | str | int) -> Decimal:
    """Валидирует цену: от 0 до 9999.99 с округлением до 2 знаков."""

    if isinstance(value, (Decimal, str, int, float)):
        amount = Decimal(str(value))

        if amount > 9999.99:
            raise ValueError("Значение не может быть больше 9999.99")

        if amount < 0:
            raise ValueError("Значение не может быть отрицательным")

        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validate_phone(phone_number: str) -> str:
    """Валидирует номер телефона: +7 или 8, затем 10 цифр."""

    if not re.fullmatch(PHONE_PATTERN, phone_number):
        raise ValueError("Неверный формат номера телефона")
    return (
        "+7" + phone_number[1:]
        if phone_number.startswith("8")
        else phone_number
    )


def validate_password(password: str) -> str:
    """Валидирует пароль: заглавная, строчная, цифра, минимум 6 символов."""

    if PASSWORD_PATTERN_RE.fullmatch(password) is None:
        raise ValueError(
            "Пароль должен содержать минимум  одну заглавную букву, "
            "одну строчную букву и одну цифру",
        )
    return password


Price = Annotated[Decimal, AfterValidator(validate_price)]
Username = Annotated[
    str, Field(pattern=USERNAME_PATTERN, min_length=3, max_length=100)
]
Phone = Annotated[str, AfterValidator(validate_phone)]
FirstAndLastName = Annotated[
    str,
    Field(pattern=FIRST_AND_LAST_NAME_PATTERN, min_length=1, max_length=100),
]
Name = Annotated[
    str, Field(pattern=NAME_PATTERN, min_length=1, max_length=100)
]
Password = Annotated[str, AfterValidator(validate_password)]
Description = Annotated[str, Field(pattern=DESCRIPTION_PATTERN)]
