"""Shared, validated city catalog. Restart the app after editing cities.json."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

CATALOG_PATH = Path(__file__).with_name("cities.json")
CityName = Annotated[str, Field(min_length=2, max_length=160)]


class CatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)


class TicketNote(CatalogModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=2000)


class CityConfig(CatalogModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$", max_length=80)
    name: CityName
    enabled: bool = True
    geocode_query: CityName | None = None
    from_label: str | None = Field(default=None, min_length=1, max_length=200)
    hero_image: str = Field(default="journey.webp", pattern=r"^[a-zA-Z0-9_-]+\.(?:webp|png|jpg|jpeg)$")
    hero_alt: str = Field(default="Город и загородный пейзаж", max_length=300)
    destination_hints: tuple[CityName, ...] = ()
    ticket_note: TicketNote | None = None

    @field_validator("destination_hints")
    @classmethod
    def unique_hints(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len({name.casefold() for name in value}) != len(value):
            raise ValueError("Подсказки направлений не должны повторяться")
        return value

    def public(self) -> dict:
        return {
            **self.model_dump(exclude={"enabled", "geocode_query", "destination_hints"}),
            "from_label": self.from_label or f"из города «{self.name}»",
        }


class CityCatalog(CatalogModel):
    default_origin: str
    cities: tuple[CityConfig, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_catalog(self) -> "CityCatalog":
        for field in ("id", "name"):
            values = [getattr(city, field).casefold() for city in self.cities]
            if len(set(values)) != len(values):
                raise ValueError(f"Города должны иметь уникальные {field}")
        if not any(city.id == self.default_origin and city.enabled for city in self.cities):
            raise ValueError("default_origin должен указывать на включённый город")
        return self

    @property
    def enabled(self) -> tuple[CityConfig, ...]:
        return tuple(city for city in self.cities if city.enabled)

    @property
    def default(self) -> CityConfig:
        return next(city for city in self.enabled if city.id == self.default_origin)

    def find(self, name: str) -> CityConfig | None:
        return next((city for city in self.cities if city.name == name), None)

    def public(self) -> dict:
        return {
            "default_origin": self.default.name,
            "origins": [city.name for city in self.enabled],
            "origin_details": [city.public() for city in self.enabled],
        }


def load_city_catalog(path: Path = CATALOG_PATH) -> CityCatalog:
    return CityCatalog.model_validate(json.loads(path.read_text(encoding="utf-8")))


@lru_cache
def get_city_catalog() -> CityCatalog:
    return load_city_catalog()


def default_origin() -> str:
    return get_city_catalog().default.name


def validate_origin(name: str) -> str:
    city = get_city_catalog().find(name)
    if city is None or not city.enabled:
        raise ValueError("Город отправления недоступен. Выберите город из списка.")
    return city.name


def origin_query(name: str) -> str:
    city = get_city_catalog().find(name)
    return (city.geocode_query or city.name) if city else name


EnabledOrigin = Annotated[
    CityName,
    AfterValidator(validate_origin),
    Field(description="Город отправления из origins в GET /api/v1/app-config."),
]

if __name__ == "__main__":
    catalog = load_city_catalog()
    print(f"Каталог корректен: доступно городов — {len(catalog.enabled)}; по умолчанию — {catalog.default.name}.")
