from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.tests.factories.model_factories import ProjectFactory, TaskFactory
from app.tests.factories.payload_factories import ProjectPayloadFactory, TaskPayloadFactory
from app.tests.utils import iso_deadline


@pytest.mark.asyncio
async def test_get_project_with_tasks(test_api_client: AsyncClient, test_db_session: AsyncSession) -> None:
    project = ProjectFactory.create()
    created_tasks = TaskFactory.create_batch(2, project=project)
    created_tasks_map = {task.id: task for task in created_tasks}
    response = await test_api_client.get(f"/api/v1/projects/{project.id}")
    assert response.status_code == status.HTTP_200_OK
    project_data = response.json()
    assert project_data["id"] == project.id
    assert project_data["title"] == project.title
    assert datetime.fromisoformat(project_data["deadline"]) == project.deadline
    assert "tasks" in project_data
    assert isinstance(project_data["tasks"], list)
    assert len(project_data["tasks"]) == len(created_tasks_map)
    for api_task_data in project_data["tasks"]:
        task_id = api_task_data["id"]
        assert task_id in created_tasks_map
        expected_task = created_tasks_map[task_id]
        assert api_task_data["title"] == expected_task.title
        assert api_task_data["description"] == expected_task.description
        assert api_task_data["completed"] == expected_task.completed
        assert datetime.fromisoformat(api_task_data["deadline"]) == expected_task.deadline


@pytest.mark.asyncio
async def test_create_project(test_api_client: AsyncClient) -> None:
    payload = ProjectPayloadFactory.as_dict()
    response = await test_api_client.post("/api/v1/projects", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["deadline"] == payload["deadline"]
    assert isinstance(data["id"], int)


@pytest.mark.asyncio
async def test_list_projects(test_api_client: AsyncClient, test_db_session: AsyncSession) -> None:
    ProjectFactory.create_batch(3)
    response = await test_api_client.get("/api/v1/projects")
    assert response.status_code == status.HTTP_200_OK
    projects = response.json()
    assert isinstance(projects, list)
    assert len(projects) == 3


@pytest.mark.asyncio
async def test_update_project(test_api_client: AsyncClient) -> None:
    project = ProjectFactory.create()
    payload = ProjectPayloadFactory.as_dict()
    response = await test_api_client.put(f"/api/v1/projects/{project.id}", json=payload)
    assert response.status_code == status.HTTP_200_OK
    updated = response.json()
    assert updated["title"] == payload["title"]
    assert updated["deadline"] == payload["deadline"]


@pytest.mark.asyncio
async def test_delete_project(test_api_client: AsyncClient, test_db_session: AsyncSession) -> None:
    project = ProjectFactory.create()
    response = await test_api_client.delete(f"/api/v1/projects/{project.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    follow_up = await test_api_client.get(f"/api/v1/projects/{project.id}")
    assert follow_up.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_nonexistent_project_returns_404(test_api_client: AsyncClient) -> None:
    response = await test_api_client.get("/api/v1/projects/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_nonexistent_project_returns_404(test_api_client: AsyncClient) -> None:
    payload = ProjectPayloadFactory.as_dict()
    response = await test_api_client.put("/api/v1/projects/99999", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_nonexistent_project_returns_404(test_api_client: AsyncClient) -> None:
    response = await test_api_client.delete("/api/v1/projects/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_project_tasks(test_api_client: AsyncClient) -> None:
    project = ProjectFactory.create()
    tasks = TaskFactory.create_batch(3, project=project)
    response = await test_api_client.get(f"/api/v1/projects/{project.id}/tasks")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(tasks)
    for task_data in data:
        assert task_data["project_id"] == project.id
        assert any(task.id == task_data["id"] for task in tasks)


@pytest.mark.asyncio
async def test_get_nonexistent_project_tasks_returns_404(test_api_client: AsyncClient) -> None:
    response = await test_api_client.get("/api/v1/projects/99999/tasks")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "Project not found" in data["detail"]


@pytest.mark.asyncio
async def test_update_project_with_invalid_deadline(test_api_client: AsyncClient) -> None:
    # Create a project with a deadline 10 days from now
    project_deadline = iso_deadline(days_from_now=10)
    project_payload = ProjectPayloadFactory.as_dict(deadline=project_deadline)
    create_resp = await test_api_client.post("/api/v1/projects", json=project_payload)
    assert create_resp.status_code == status.HTTP_201_CREATED
    project_data = create_resp.json()
    project_id = project_data["id"]

    # Create a task for the project with a deadline 8 days from now
    task_deadline = iso_deadline(days_from_now=8)
    task_payload = TaskPayloadFactory.as_dict(project_id=project_id, deadline=task_deadline)
    task_resp = await test_api_client.post("/api/v1/tasks", json=task_payload)
    assert task_resp.status_code == status.HTTP_201_CREATED

    # Attempt to update the project's deadline to 7 days from now (which is earlier than the task's deadline)
    new_project_deadline = iso_deadline(days_from_now=7)
    update_payload = ProjectPayloadFactory.as_dict(deadline=new_project_deadline)
    update_resp = await test_api_client.put(f"/api/v1/projects/{project_id}", json=update_payload)

    assert update_resp.status_code == status.HTTP_400_BAD_REQUEST
    data = update_resp.json()
    # Expected error message should mention the task's deadline being later than the new project deadline
    assert "has a deadline later than the project deadline" in data["detail"]
