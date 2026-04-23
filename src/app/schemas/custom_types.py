import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import AfterValidator, Field

from app.constants import (
    DESCRIPTION_PATTERN,
    PHONE_PATTERN,
    USERNAME_PATTERN,
    FIRST_AND_LAST_NAME_PATTERN,
)

PASSWORD_PATTERN = re.compile(
    r"^"
    r"(?=.*[A-Z])"
    r"(?=.*[a-z])"
    r"(?=.*\d)"
    r"\S{6,}$",
)

NAME_PATTERN = re.compile(
    r"^"
    r"(?:[а-яА-ЯёЁ]+(?:[ -][а-яА-ЯёЁ]+)*"
    r"|"
    r"[A-Za-z]+(?:[ -][A-Za-z]+)*)"
    r"$",
)


def validate_price(value: Decimal | float | str | int) -> Decimal:
    if isinstance(value, (Decimal, str, int, float)):
        amount = Decimal(str(value))

        if amount < 0:
            raise ValueError("Значение не может быть отрицательным")

        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validate_phone(phone_number: str) -> str:
    if not re.fullmatch(PHONE_PATTERN, phone_number):
        raise ValueError("Неверный формат номера телефона")
    return (
        "+7" + phone_number[1:]
        if phone_number.startswith("8")
        else phone_number
    )


def validate_password(password: str) -> str:
    if PASSWORD_PATTERN.fullmatch(password) is None:
        raise ValueError(
            "Пароль должен содержать минимум  одну заглавную букву, "
            "одну строчную букву и одну цифру",
        )
    return password


Price = Annotated[Decimal, AfterValidator(validate_price)]
Username = Annotated[str, Field(pattern=USERNAME_PATTERN)]
Phone = Annotated[str, AfterValidator(validate_phone)]
FirstAndLastName = Annotated[
    str,
    Field(pattern=FIRST_AND_LAST_NAME_PATTERN, min_length=1, max_length=100),
]
Name = Annotated[
    str, Field(pattern=NAME_PATTERN.pattern, min_length=1, max_length=100)
]
Password = Annotated[str, AfterValidator(validate_password)]
Description = Annotated[str, Field(pattern=DESCRIPTION_PATTERN)]
