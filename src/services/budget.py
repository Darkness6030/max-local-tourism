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
    TransportOptions,
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
    transport: TransportOptions | None = None,
) -> tuple[BudgetSummary, Accommodation | None]:
    # The model is asked to exclude lodging: discard accidental duplicates as well.
    items = [
        item.model_copy()
        for item in generated.budget_items
        if not any(word in item.category.casefold() for word in LODGING_CATEGORY_WORDS)
    ]

    if not request.has_car:
        items = [item for item in items if not _intercity_category(item.category)]
        outbound = transport.outbound[0].price_rub if transport and transport.outbound else None
        inbound = transport.return_trip[0].price_rub if transport and transport.return_trip else None
        out_estimated, back_estimated = outbound is None, inbound is None
        outbound = outbound if outbound is not None else generated.outbound_fare_rub
        inbound = inbound if inbound is not None else generated.return_fare_rub
        # If only one direction can be priced, use it as an explicit estimate for the other.
        outbound = outbound if outbound is not None else inbound
        inbound = inbound if inbound is not None else outbound
        if outbound is not None and inbound is not None:
            amount = ceil((outbound + inbound) * request.travelers)
            comment = f"(Туда {outbound:g} ₽ + обратно {inbound:g} ₽) × {request.travelers} чел. Без льгот."
            if out_estimated or back_estimated:
                estimated = "туда и обратно" if out_estimated and back_estimated else "туда" if out_estimated else "обратно"
                comment += f" Стоимость {estimated} — оценка, уточните тариф."
            items.append(BudgetItem(category="intercity_transport", amount_rub=amount, comment=comment))
        else:
            items.append(BudgetItem(category="intercity_transport", amount_rub=0,
                                    comment="Стоимость дороги туда и обратно неизвестна и не включена в итог. Уточните у перевозчика."))

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

        items.append(BudgetItem(category="lodging", amount_rub=lodging_total))

    subtotal = sum(item.amount_rub for item in items)
    reserve = ceil(subtotal * BUDGET_RESERVE_PERCENT / 100)
    items.append(BudgetItem(category="reserve", amount_rub=reserve))

    total = subtotal + reserve
    return BudgetSummary(
        limit_rub=request.budget_rub,
        estimated_total_rub=total,
        per_person_rub=ceil(total / request.travelers),
        within_budget=total <= request.budget_rub,
        items=items,
    ), accommodation


def _intercity_category(category: str) -> bool:
    category = category.casefold().strip()
    if any(word in category for word in ("местн", "городской", "такси", "метро", "входн", "музе")) and "междугород" not in category:
        return False
    return category.startswith(("транспорт", "проезд")) or category in {"дорога", "transport", "intercity_transport"} or any(
        word in category for word in ("междугород", "дорога", "электрич", "автобус", "ж/д", "железнодорож", "билеты на поезд")
    )
