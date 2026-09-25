from datetime import timedelta

import pytest
from pydantic import ValidationError

from src.models import TimelineItem, TripRequest, current_date


def test_trip_request_has_dynamic_future_default() -> None:
    request = TripRequest(origin="Москва")
    assert request.start_date == current_date() + timedelta(days=1)


def test_trip_request_rejects_past_date() -> None:
    with pytest.raises(ValidationError, match="не может быть в прошлом"):
        TripRequest(origin="Москва", start_date=current_date() - timedelta(days=1))


def test_trip_request_rejects_unsupported_origin() -> None:
    with pytest.raises(ValidationError):
        TripRequest(origin="Казань")


def test_children_require_family_group() -> None:
    with pytest.raises(ValidationError, match="group_type=family"):
        TripRequest(origin="Москва", children_ages=[7], group_type="friends")


def test_gigachat_time_with_seconds_is_normalized() -> None:
    item = TimelineItem(
        start_time="09:25:00",
        end_time="11:15:00",
        title="Прогулка",
        place="Центр города",
        description="Спокойная прогулка по историческому центру.",
        indoor=False,
    )

    assert item.start_time == "09:25"
    assert item.end_time == "11:15"
