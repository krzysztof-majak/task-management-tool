from datetime import datetime, timedelta, timezone

import pytest
from factory import Factory

from app.tests.factories.payload_factories import ModelType, ProjectPayloadFactory, TaskPayloadFactory
from app.tests.utils import convert_datetimes, iso_deadline


@pytest.mark.parametrize(
    "days_from_now",
    [0, 1, -1, 7],
)
def test_iso_deadline_format_and_offset(days_from_now: int) -> None:
    result = iso_deadline(days_from_now=days_from_now)
    expected = datetime.now(timezone.utc) + timedelta(days=days_from_now)

    expected = expected.replace(tzinfo=None)

    parsed = datetime.fromisoformat(result)
    assert isinstance(result, str)
    assert abs((parsed - expected).total_seconds()) < 2  # Allow 2 second margin for runtime delay


@pytest.mark.parametrize(
    "factory_class, datetime_keys",
    [
        (ProjectPayloadFactory, ["deadline"]),
        (TaskPayloadFactory, ["deadline"]),
    ],
)
def test_convert_datetimes_on_factory_payload(factory_class: Factory[ModelType], datetime_keys: str) -> None:
    model_instance = factory_class.build()
    input_dict = model_instance.model_dump()

    result = convert_datetimes(input_dict)

    for key in datetime_keys:
        assert key in result
        assert isinstance(result[key], str)
        parsed = datetime.fromisoformat(result[key])
        assert isinstance(parsed, datetime)
