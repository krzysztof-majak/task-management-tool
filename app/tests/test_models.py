from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Task
from app.tests.factories.payload_factories import ProjectPayloadFactory, TaskPayloadFactory


@pytest.mark.asyncio
async def test_project_creation(test_db_session: AsyncSession) -> None:
    project_payload = ProjectPayloadFactory.build()
    project = Project(**project_payload.model_dump())
    test_db_session.add(project)
    await test_db_session.commit()

    await test_db_session.refresh(project)

    assert project.id is not None
    assert project.title == project_payload.title
    assert project.deadline == project_payload.deadline
    assert project.tasks == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"description": None, "deadline": None, "project_id": None},
        {"description": "Only description"},
        {"deadline": datetime(2025, 7, 1)},
        {"completed": True},
    ],
    ids=[
        "create_default",
        "create_all_null",
        "create_only_description",
        "create_only_deadline",
        "create_only_completed",
    ],
)
async def test_task_creation(test_db_session: AsyncSession, overrides: dict[str, Any]) -> None:
    payload = TaskPayloadFactory.build(**overrides)
    task = Task(**payload.model_dump())
    test_db_session.add(task)
    await test_db_session.commit()
    await test_db_session.refresh(task)

    for field, expected_value in overrides.items():
        actual = getattr(task, field)
        assert actual == expected_value, f"{field} mismatch: {actual!r} != {expected_value!r}"

    assert task.id is not None
    assert task.title == payload.title
    assert task.completed == payload.completed
    assert task.description == payload.description
    assert task.deadline == payload.deadline
    assert task.project_id == payload.project_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides, field_to_update, new_value",
    [
        ({"completed": False}, "completed", True),
        ({"description": None}, "description", "Write unit tests for reporting module"),
        ({"deadline": None}, "deadline", datetime(2025, 12, 31)),
    ],
    ids=[
        "update_completed_False_to_True",
        "update_description_None_to_string",
        "update_deadline_None_to_datetime",
    ],
)
async def test_task_update(
    test_db_session: AsyncSession,
    overrides: dict[str, Any],
    field_to_update: str,
    new_value: str,
) -> None:
    payload = TaskPayloadFactory.build(**overrides)
    task = Task(**payload.model_dump())
    test_db_session.add(task)
    await test_db_session.commit()
    await test_db_session.refresh(task)

    assert getattr(task, field_to_update) == overrides[field_to_update], (
        f"Initial value for {field_to_update} was incorrect"
    )

    setattr(task, field_to_update, new_value)
    test_db_session.add(task)
    await test_db_session.commit()
    await test_db_session.refresh(task)

    assert getattr(task, field_to_update) == new_value, f"Update failed for {field_to_update}"

    assert task.title == payload.title
    assert task.completed is not None  # may be changed, but not None
    assert task.description == task.description
    assert task.deadline == task.deadline
    assert task.project_id == task.project_id


@pytest.mark.asyncio
async def test_project_tasks_relationship_and_retrieval(test_db_session: AsyncSession) -> None:
    # Create and persist a project
    project_payload = ProjectPayloadFactory.build()
    project = Project(**project_payload.model_dump())
    test_db_session.add(project)
    await test_db_session.flush()

    # Create randomized task payloads and associate with the project
    tasks_payloads = [TaskPayloadFactory.build(deadline=None) for _ in range(2)]
    expected_titles = [payload.title for payload in tasks_payloads]

    for payload in tasks_payloads:
        task_data = payload.model_dump()
        task_data.pop("project_id", None)
        task = Task(**task_data, project=project)
        test_db_session.add(task)

    await test_db_session.commit()
    test_db_session.expire_all()

    # Fetch the project and verify relationships
    result = await test_db_session.execute(select(Project).where(Project.title == project_payload.title))
    fetched_project = result.scalars().first()
    assert fetched_project is not None

    fetched_titles = {task.title for task in fetched_project.tasks}
    assert set(expected_titles) == fetched_titles

    for task in fetched_project.tasks:
        assert task.project_id == fetched_project.id
        assert task.project == fetched_project
