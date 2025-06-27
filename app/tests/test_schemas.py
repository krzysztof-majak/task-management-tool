from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pytest
from pydantic import BaseModel, ValidationError

from app.schemas import (
    DateTimeValidatorMixin,
    Project,
    ProjectCreate,
    ProjectUpdate,
    Task,
    TaskBase,
    TaskCreate,
    TaskUpdate,
)
from app.tests.factories.payload_factories import ProjectPayloadFactory, TaskPayloadFactory


def test_remove_tzinfo() -> None:
    """
    Tests that the remove_tzinfo validator correctly converts a timezone-aware
    datetime to a naive UTC datetime when used directly in a model.
    """

    class TestModel(BaseModel, DateTimeValidatorMixin):
        deadline: Optional[datetime] = None

    # Test with a timezone-aware datetime (e.g., UTC+3)
    tz_aware_now = datetime.now(timezone(timedelta(hours=3)))
    model_instance = TestModel(deadline=tz_aware_now)
    expected_naive_utc = tz_aware_now.astimezone(timezone.utc).replace(tzinfo=None)

    assert model_instance.deadline is not None
    assert model_instance.deadline.tzinfo is None
    assert model_instance.deadline == expected_naive_utc

    # Test with a timezone-naive datetime (should remain unchanged)
    naive_dt = datetime(2024, 7, 1, 10, 0, 0)
    model_instance_naive = TestModel(deadline=naive_dt)
    assert model_instance_naive.deadline == naive_dt
    assert model_instance_naive.deadline.tzinfo is None

    # Test with None (should remain None)
    model_instance_none = TestModel(deadline=None)
    assert model_instance_none.deadline is None


# --- Project Schema Tests ---
def test_project_create_valid() -> None:
    """Tests successful creation of ProjectCreate schema with valid data using factory."""
    project_data = ProjectPayloadFactory.as_dict()
    project = ProjectCreate(**project_data)

    assert project.title == project_data["title"]
    assert project.deadline == datetime.fromisoformat(project_data["deadline"]).replace(tzinfo=None)


def test_project_create_with_tz_aware_deadline() -> None:
    """Tests ProjectCreate with a timezone-aware deadline, ensuring tzinfo removal."""
    # Create a timezone-aware datetime (e.g., UTC)
    tz_aware_deadline = datetime(2025, 12, 31, 10, 0, 0, tzinfo=timezone.utc)
    project_data = ProjectPayloadFactory.as_dict(deadline=tz_aware_deadline)
    project = ProjectCreate(**project_data)

    # The deadline should be timezone-naive after validation
    assert project.deadline == tz_aware_deadline.replace(tzinfo=None)
    assert project.deadline.tzinfo is None

    # Test with a different timezone (e.g., CET - UTC+1)
    cet_offset = timedelta(hours=1)
    cet_tz = timezone(cet_offset)
    tz_aware_deadline_cet = datetime(2025, 12, 31, 10, 0, 0, tzinfo=cet_tz)
    project_data_cet = ProjectPayloadFactory.as_dict(deadline=tz_aware_deadline_cet)
    project_cet = ProjectCreate(**project_data_cet)

    # It should convert to UTC and then remove tzinfo
    expected_utc_naive = (tz_aware_deadline_cet - cet_offset).replace(tzinfo=None)
    assert project_cet.deadline == expected_utc_naive
    assert project_cet.deadline.tzinfo is None


def test_project_create_missing_title() -> None:
    """Tests ProjectCreate failure when 'title' is missing (required field)."""
    with pytest.raises(ValidationError):
        # Create data and then remove the required 'title' field
        data = ProjectPayloadFactory.as_dict()
        data.pop("title")
        ProjectCreate(**data)


def test_project_create_missing_deadline() -> None:
    """Tests ProjectCreate failure when 'deadline' is missing (required field)."""
    with pytest.raises(ValidationError):
        # Create data and then remove the required 'deadline' field
        data = ProjectPayloadFactory.as_dict()
        data.pop("deadline")
        ProjectCreate(**data)


def test_project_update_all_optional() -> None:
    """Tests ProjectUpdate where all fields are optional and can be omitted."""
    # No fields provided
    project_update_empty = ProjectUpdate()
    assert project_update_empty.title is None
    assert project_update_empty.deadline is None

    # Only title provided
    project_update_title = ProjectUpdate(title="Updated Title")
    assert project_update_title.title == "Updated Title"
    assert project_update_title.deadline is None

    # Only deadline provided
    new_deadline = datetime(2026, 1, 1).replace(microsecond=0)
    project_update_deadline = ProjectUpdate(deadline=new_deadline)
    assert project_update_deadline.title is None
    assert project_update_deadline.deadline == new_deadline


def test_project_full_schema() -> None:
    """Tests the full Project schema, including 'id' and 'tasks'."""
    task_data: dict[str, Any] = {"id": 1, "title": "Task 1", "completed": False}
    project_data: dict[str, Any] = {
        "id": 10,
        "title": "Full Project",
        "deadline": datetime(2025, 12, 31).isoformat(),
        "tasks": [task_data],
    }

    project = Project(**project_data)
    assert project.id == 10
    assert project.title == "Full Project"
    assert isinstance(project.deadline, datetime)
    assert len(project.tasks) == 1
    assert project.tasks[0].title == "Task 1"
    assert project.tasks[0].id == 1


# --- Task Schema Tests ---
def test_deadline_timezone_removal() -> None:
    """
    Tests that the deadline field in TaskBase correctly removes timezone information.
    """
    dt_with_tz = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)

    task = TaskBase(title="Test Task", deadline=dt_with_tz)
    assert task.deadline is not None
    assert task.deadline.tzinfo is None
    assert task.deadline == dt_with_tz.replace(tzinfo=None)


def test_task_create_valid() -> None:
    """Tests successful creation of TaskCreate schema with valid data using factory."""
    task_data = TaskPayloadFactory.as_dict()
    task = TaskCreate(**task_data)
    assert task.title == task_data["title"]
    assert task.description == task_data["description"]
    assert task.deadline == datetime.fromisoformat(task_data["deadline"]).replace(tzinfo=None)
    assert task.completed is False
    assert task.project_id is None


def test_task_create_with_all_fields() -> None:
    """Tests TaskCreate with all optional fields provided using factory."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    task_data = TaskPayloadFactory.as_dict(
        description="Prepare annual report.",
        deadline=now,
        completed=True,
        project_id=1,
    )
    task = TaskCreate(**task_data)
    assert task.title == task_data["title"]
    assert task.description == "Prepare annual report."
    assert task.deadline == now.replace(tzinfo=None)  # Expect naive UTC
    assert task.completed is True
    assert task.project_id == 1


def test_task_create_with_tz_aware_deadline() -> None:
    """Tests TaskCreate with a timezone-aware deadline, ensuring tzinfo removal."""
    tz_aware_deadline = datetime(2025, 10, 10, 15, 30, 0, tzinfo=timezone.utc)
    task_data = TaskPayloadFactory.as_dict(deadline=tz_aware_deadline)
    task = TaskCreate(**task_data)

    assert task.deadline == tz_aware_deadline.replace(tzinfo=None)
    assert task.deadline.tzinfo is None


def test_task_create_missing_title() -> None:
    """Tests TaskCreate failure when 'title' is missing (required field)."""
    with pytest.raises(ValidationError):
        data = TaskPayloadFactory.as_dict()
        data.pop("title")
        TaskCreate(**data)


def test_optional_fields_in_task_update() -> None:
    """
    Tests that optional fields in TaskUpdate correctly remain None when not provided.
    """
    update_data = TaskUpdate(title="Updated Title")
    assert update_data is not None
    assert update_data.title == "Updated Title"
    assert update_data.deadline is None
    assert update_data.description is None
    assert update_data.completed is None
    assert update_data.project_id is None

    update_data_explicit_none = TaskUpdate(description=None, completed=None)
    assert update_data_explicit_none.description is None
    assert update_data_explicit_none.completed is None


def test_task_update_all_optional() -> None:
    """Tests TaskUpdate where all fields are optional and can be omitted."""
    # No fields provided
    task_update_empty = TaskUpdate()
    assert task_update_empty.title is None
    assert task_update_empty.description is None
    assert task_update_empty.deadline is None
    assert task_update_empty.completed is None
    assert task_update_empty.project_id is None

    # Partial update
    task_update_partial = TaskUpdate(title="Revised Task", completed=True)
    assert task_update_partial.title == "Revised Task"
    assert task_update_partial.completed is True
    assert task_update_partial.description is None


def test_task_full_schema() -> None:
    """Tests the full Task schema, including 'id' and ORM compatibility."""
    task_data: dict[str, Any] = {
        "id": 5,
        "title": "Complete Milestone",
        "description": "Finalize phase 1.",
        "deadline": datetime(2025, 9, 1).isoformat(),
        "completed": True,
        "project_id": 100,
    }

    task = Task(**task_data)
    assert task.id == 5
    assert task.title == "Complete Milestone"
    assert task.description == "Finalize phase 1."
    assert isinstance(task.deadline, datetime)
    assert task.completed is True
    assert task.project_id == 100
