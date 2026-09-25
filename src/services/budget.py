"""Group estimates and an explicit reserve, separate from provider ticket prices."""

from datetime import timedelta
from math import ceil

from src.constants import (
    BUDGET_RESERVE_PERCENT,
    DEFAULT_ROOM_NIGHT_RUB,
    TRAVELERS_PER_ROOM,
)
from src.models import (
    Accommodation,
    BudgetItem,
    BudgetSummary,
    GeneratedTripContent,
    GeoPoint,
    TripRequest,
)
from src.services.hotels import HotelCatalog, hotel_search_url

LODGING_CATEGORY_WORDS = (
    "прожив",
    "ночлег",
    "ночёв",
    "ночев",
    "гостини",
    "отел",
    "жиль",
)


def build_budget(
    generated: GeneratedTripContent,
    request: TripRequest,
    destination: GeoPoint,
    catalog: HotelCatalog | None,
) -> tuple[BudgetSummary, Accommodation | None]:
    # The model is asked to exclude lodging: discard accidental duplicates as well.
    items = [
        item.model_copy()
        for item in generated.budget_items
        if not any(word in item.category.casefold() for word in LODGING_CATEGORY_WORDS)
    ]

    accommodation = None
    if request.days > 1:
        nights = request.days - 1
        rooms = ceil(request.travelers / TRAVELERS_PER_ROOM)
        nightly = generated.lodging_nightly_rub or DEFAULT_ROOM_NIGHT_RUB
        lodging_total = nightly * nights * rooms
        catalog = catalog or HotelCatalog([], available=False)
        status = "unavailable"
        if catalog.available:
            status = "found" if catalog.hotels else "empty"

        accommodation = Accommodation(
            check_in=request.start_date,
            check_out=request.start_date + timedelta(days=nights),
            nights=nights,
            rooms=rooms,
            estimated_room_night_rub=nightly,
            estimated_total_rub=lodging_total,
            status=status,
            hotels=catalog.hotels,
            search_url=hotel_search_url(destination),
            fetched_at=catalog.fetched_at,
        )

        items.append(
            BudgetItem(
                category="Проживание",
                amount_rub=lodging_total,
                comment=f"{rooms} ном. × {nights} ноч. × ≈{nightly} ₽",
            )
        )

    subtotal = sum(item.amount_rub for item in items)
    reserve = ceil(subtotal * BUDGET_RESERVE_PERCENT / 100)
    items.append(
        BudgetItem(
            category="Небольшой запас",
            amount_rub=reserve,
            comment="На непредвиденные расходы.",
        )
    )

    total = subtotal + reserve
    return BudgetSummary(
        limit_rub=request.budget_rub,
        estimated_total_rub=total,
        per_person_rub=ceil(total / request.travelers),
        within_budget=total <= request.budget_rub,
        items=items,
        disclaimer="Ориентировочные расходы на всю группу. Цены мест, билетов и проживания уточняйте перед поездкой.",
    ), accommodation
