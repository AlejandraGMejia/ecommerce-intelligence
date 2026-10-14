"""Test delivery rules using Olist's timezone-naive timestamps."""

from datetime import datetime


def source_datetime(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
) -> datetime:
    """Create a timestamp matching the Olist source format."""
    return datetime(year, month, day, hour, minute)  # noqa: DTZ001 - Olist timestamps have no timezone.


def is_valid_delivery(
    purchase_date: datetime | None,
    delivery_date: datetime | None,
    estimated_date: datetime | None,
    carrier_date: datetime | None = None,
) -> bool:
    """Apply the same chronological checks as our SQL queries."""
    if purchase_date is None or delivery_date is None or estimated_date is None:
        return False

    if delivery_date < purchase_date:
        return False

    return carrier_date is None or delivery_date >= carrier_date


def is_late_delivery(
    delivery_date: datetime,
    estimated_date: datetime,
) -> bool:
    """Classify lateness by calendar date, not by hour."""
    return delivery_date.date() > estimated_date.date()


def test_valid_delivery() -> None:
    """Accept chronologically consistent timestamps."""
    assert is_valid_delivery(
        purchase_date=source_datetime(2018, 3, 1),
        delivery_date=source_datetime(2018, 3, 10),
        estimated_date=source_datetime(2018, 3, 15),
        carrier_date=source_datetime(2018, 3, 3),
    )


def test_missing_delivery_date() -> None:
    """Reject deliveries without an actual delivery timestamp."""
    assert not is_valid_delivery(
        purchase_date=source_datetime(2018, 3, 1),
        delivery_date=None,
        estimated_date=source_datetime(2018, 3, 15),
    )


def test_missing_estimated_date() -> None:
    """Reject deliveries without an estimated delivery date."""
    assert not is_valid_delivery(
        purchase_date=source_datetime(2018, 3, 1),
        delivery_date=source_datetime(2018, 3, 10),
        estimated_date=None,
    )


def test_delivery_before_purchase() -> None:
    """Reject delivery dates earlier than purchase dates."""
    assert not is_valid_delivery(
        purchase_date=source_datetime(2018, 3, 10),
        delivery_date=source_datetime(2018, 3, 5),
        estimated_date=source_datetime(2018, 3, 15),
    )


def test_delivery_before_carrier() -> None:
    """Reject inconsistent carrier and delivery timestamps."""
    assert not is_valid_delivery(
        purchase_date=source_datetime(2018, 3, 1),
        delivery_date=source_datetime(2018, 3, 5),
        estimated_date=source_datetime(2018, 3, 15),
        carrier_date=source_datetime(2018, 3, 8),
    )


def test_delivery_without_carrier_date() -> None:
    """Allow valid deliveries with missing carrier timestamps."""
    assert is_valid_delivery(
        purchase_date=source_datetime(2018, 3, 1),
        delivery_date=source_datetime(2018, 3, 10),
        estimated_date=source_datetime(2018, 3, 15),
        carrier_date=None,
    )


def test_delivery_on_estimated_date_is_on_time() -> None:
    """An order delivered on the estimated day is on time."""
    assert not is_late_delivery(
        delivery_date=source_datetime(2018, 3, 15, 23, 30),
        estimated_date=source_datetime(2018, 3, 15),
    )


def test_delivery_after_estimated_date_is_late() -> None:
    """An order delivered the following day is late."""
    assert is_late_delivery(
        delivery_date=source_datetime(2018, 3, 16),
        estimated_date=source_datetime(2018, 3, 15),
    )
