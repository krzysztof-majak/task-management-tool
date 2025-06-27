import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.tests.factories.model_factories import ProjectFactory, TaskFactory
from app.tests.factories.payload_factories import ProjectPayloadFactory, TaskPayloadFactory
from app.tests.utils import iso_deadline


@pytest.mark.asyncio
async def test_get_tasks(test_api_client: AsyncClient, test_db_session: AsyncSession) -> None:
    TaskFactory.create_batch(5)

    response = await test_api_client.get("/api/v1/tasks")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5


@pytest.mark.asyncio
async def test_get_tasks_with_pagination(test_api_client: AsyncClient, test_db_session: AsyncSession) -> None:
    TaskFactory.create_batch(10)

    response = await test_api_client.get("/api/v1/tasks?skip=0&limit=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5


@pytest.mark.asyncio
async def test_get_tasks_with_deadlines(test_api_client: AsyncClient) -> None:
    # Create 2 tasks with deadlines
    task1_payload = TaskPayloadFactory.as_dict(deadline=iso_deadline(2))
    task2_payload = TaskPayloadFactory.as_dict(deadline=iso_deadline(4))
    resp1 = await test_api_client.post("/api/v1/tasks", json=task1_payload)
    resp2 = await test_api_client.post("/api/v1/tasks", json=task2_payload)
    assert resp1.status_code == status.HTTP_201_CREATED
    assert resp2.status_code == status.HTTP_201_CREATED

    # Create 1 task without a deadline
    no_deadline_payload = TaskPayloadFactory.as_dict()
    no_deadline_payload.pop("deadline", None)
    resp3 = await test_api_client.post("/api/v1/tasks", json=no_deadline_payload)
    assert resp3.status_code == status.HTTP_201_CREATED

    # Now fetch only tasks with deadlines
    response = await test_api_client.get("/api/v1/tasks/deadlines")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # Only 2 tasks should be returned

    for task in data:
        assert task["deadline"] is not None


@pytest.mark.asyncio
async def test_get_task_by_id(test_api_client: AsyncClient) -> None:
    task = TaskFactory.create()
    response = await test_api_client.get(f"/api/v1/tasks/{task.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == task.id
    assert data["title"] == task.title
    assert data["description"] == task.description
    assert task.deadline is not None
    assert data["deadline"] == task.deadline.isoformat()
    assert data["completed"] == task.completed
    assert data["project_id"] == task.project_id


@pytest.mark.asyncio
async def test_get_nonexistent_task_by_id_returns_404(test_api_client: AsyncClient) -> None:
    response = await test_api_client.get("/api/v1/tasks/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "Task not found" in data["detail"]


@pytest.mark.asyncio
async def test_create_task(test_api_client: AsyncClient, test_db_session: AsyncSession) -> None:
    project = ProjectFactory.create()
    payload = TaskPayloadFactory.as_dict(project_id=project.id)
    response = await test_api_client.post("/api/v1/tasks", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["deadline"] == payload["deadline"]
    assert data["completed"] == payload["completed"]
    assert data["project_id"] == payload["project_id"]


@pytest.mark.asyncio
async def test_create_task_assigned_to_existing_project(test_api_client: AsyncClient) -> None:
    project_deadline = iso_deadline(10)
    project_payload = ProjectPayloadFactory.as_dict(deadline=project_deadline)
    project_resp = await test_api_client.post("/api/v1/projects", json=project_payload)
    assert project_resp.status_code == status.HTTP_201_CREATED
    project_id = project_resp.json()["id"]

    task_deadline = iso_deadline(7)
    task_payload = TaskPayloadFactory.as_dict(deadline=task_deadline, project_id=project_id)

    task_resp = await test_api_client.post("/api/v1/tasks", json=task_payload)
    assert task_resp.status_code == status.HTTP_201_CREATED

    data = task_resp.json()
    assert data["title"] == task_payload["title"]
    assert data["project_id"] == project_id
    assert data["deadline"] == task_payload["deadline"]


@pytest.mark.asyncio
async def test_create_task_assigned_to_nonexistent_project_returns_404(test_api_client: AsyncClient) -> None:
    payload = TaskPayloadFactory.as_dict(project_id=99999)
    response = await test_api_client.post("/api/v1/tasks", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "Project not found" in data["detail"]


@pytest.mark.asyncio
async def test_create_task_with_invalid_deadline(test_api_client: AsyncClient) -> None:
    # Create a project with a deadline 5 days from now
    project_deadline = iso_deadline(days_from_now=5)
    project_payload = ProjectPayloadFactory.as_dict(deadline=project_deadline)
    resp = await test_api_client.post("/api/v1/projects", json=project_payload)
    assert resp.status_code == status.HTTP_201_CREATED
    project_data = resp.json()
    project_id = project_data["id"]

    # Create a task with a deadline 7 days from now (which is later than the project's deadline)
    task_deadline = iso_deadline(days_from_now=7)
    task_payload = TaskPayloadFactory.as_dict(project_id=project_id, deadline=task_deadline)
    resp = await test_api_client.post("/api/v1/tasks", json=task_payload)

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert "Task deadline cannot be later than project deadline" in data["detail"]


@pytest.mark.asyncio
async def test_update_task(test_api_client: AsyncClient) -> None:
    task = TaskFactory.create()
    payload = TaskPayloadFactory.as_dict()
    response = await test_api_client.put(f"/api/v1/tasks/{task.id}", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["deadline"] == payload["deadline"]
    assert data["completed"] == payload["completed"]
    assert data["project_id"] == payload["project_id"]


@pytest.mark.asyncio
async def test_update_task_with_invalid_deadline(test_api_client: AsyncClient) -> None:
    # Create a project with a deadline 7 days from now
    project_deadline = iso_deadline(days_from_now=7)
    project_payload = ProjectPayloadFactory.as_dict(deadline=project_deadline)
    project_resp = await test_api_client.post("/api/v1/projects", json=project_payload)
    assert project_resp.status_code == status.HTTP_201_CREATED
    project_id = project_resp.json()["id"]

    # Create a task with a deadline 5 days from now
    task_deadline = iso_deadline(days_from_now=5)
    task_payload = TaskPayloadFactory.as_dict(project_id=project_id, deadline=task_deadline)
    task_resp = await test_api_client.post("/api/v1/tasks", json=task_payload)
    assert task_resp.status_code == status.HTTP_201_CREATED
    task_id = task_resp.json()["id"]

    # Attempt to update the task's deadline to 10 days from now (which is later than the project's deadline)
    new_task_deadline = iso_deadline(days_from_now=10)
    update_payload = TaskPayloadFactory.as_dict(deadline=new_task_deadline, project_id=project_id)
    update_resp = await test_api_client.put(f"/api/v1/tasks/{task_id}", json=update_payload)

    assert update_resp.status_code == status.HTTP_400_BAD_REQUEST
    data = update_resp.json()
    assert "Task deadline cannot be later than project deadline" in data["detail"]


@pytest.mark.asyncio
async def test_update_nonexistent_task_returns_404(test_api_client: AsyncClient) -> None:
    payload = TaskPayloadFactory.as_dict()
    response = await test_api_client.put("/api/v1/tasks/99999", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "Task not found" in data["detail"]


@pytest.mark.asyncio
async def test_update_task_link_to_nonexistent_returns_404(test_api_client: AsyncClient) -> None:
    task = TaskFactory.create()
    payload = TaskPayloadFactory.as_dict(project_id=99999)
    response = await test_api_client.put(f"/api/v1/tasks/{task.id}", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "Project not found" in data["detail"]


@pytest.mark.asyncio
async def test_delete_task(test_api_client: AsyncClient) -> None:
    task = TaskFactory.create()
    response = await test_api_client.delete(f"/api/v1/tasks/{task.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    follow_up = await test_api_client.get(f"/api/v1/tasks/{task.id}")
    assert follow_up.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_nonexistent_task_returns_404(test_api_client: AsyncClient) -> None:
    response = await test_api_client.delete("/api/v1/tasks/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_link_task_to_project(test_api_client: AsyncClient) -> None:
    # Create a project
    project_payload = ProjectPayloadFactory.as_dict(deadline=iso_deadline(5))
    project_resp = await test_api_client.post("/api/v1/projects", json=project_payload)
    assert project_resp.status_code == status.HTTP_201_CREATED
    project_id = project_resp.json()["id"]

    # Create a task with no project_id but an earlier deadline
    task_payload = TaskPayloadFactory.as_dict(deadline=iso_deadline(3), project_id=None)
    task_resp = await test_api_client.post("/api/v1/tasks", json=task_payload)
    assert task_resp.status_code == status.HTTP_201_CREATED
    task_id = task_resp.json()["id"]

    # Link task to project
    link_resp = await test_api_client.post(f"/api/v1/tasks/{task_id}/link-project/{project_id}")
    assert link_resp.status_code == status.HTTP_200_OK

    data = link_resp.json()
    assert data["id"] == task_id
    assert data["project_id"] == project_id


@pytest.mark.asyncio
async def test_link_task_to_project_with_invalid_deadline(test_api_client: AsyncClient) -> None:
    # Create a project with a deadline 5 days from now
    project_deadline = iso_deadline(days_from_now=5)
    project_payload = ProjectPayloadFactory.as_dict(deadline=project_deadline)
    proj_resp = await test_api_client.post("/api/v1/projects", json=project_payload)
    assert proj_resp.status_code == status.HTTP_201_CREATED
    project_data = proj_resp.json()
    project_id = project_data["id"]

    # Create a task (without a project) with a deadline 7 days from now
    task_deadline = iso_deadline(days_from_now=7)
    task_payload = TaskPayloadFactory.as_dict(deadline=task_deadline, project_id=None)
    task_resp = await test_api_client.post("/api/v1/tasks", json=task_payload)
    assert task_resp.status_code == status.HTTP_201_CREATED
    task_data = task_resp.json()
    task_id = task_data["id"]

    # Attempt to link the task to the project. This should fail because task_deadline (7 days) > project_deadline (5 days)
    link_resp = await test_api_client.post(f"/api/v1/tasks/{task_id}/link-project/{project_id}")
    assert link_resp.status_code == status.HTTP_400_BAD_REQUEST
    data = link_resp.json()
    assert "Task deadline cannot be later than project deadline." in data["detail"]


@pytest.mark.asyncio
async def test_link_task_to_nonexistent_project_returns_404(test_api_client: AsyncClient) -> None:
    # Create a task with no project_id
    task_payload = TaskPayloadFactory.as_dict(project_id=None)
    task_resp = await test_api_client.post("/api/v1/tasks", json=task_payload)
    assert task_resp.status_code == status.HTTP_201_CREATED
    task_id = task_resp.json()["id"]

    # Attempt to link the task to a nonexistent project
    link_resp = await test_api_client.post(f"/api/v1/tasks/{task_id}/link-project/99999")
    assert link_resp.status_code == status.HTTP_404_NOT_FOUND
    data = link_resp.json()
    assert "Project not found" in data["detail"]


@pytest.mark.asyncio
async def test_link_nonexistent_task_to_project_returns_404(test_api_client: AsyncClient) -> None:
    # Create a project
    project_payload = ProjectPayloadFactory.as_dict(deadline=iso_deadline(5))
    project_resp = await test_api_client.post("/api/v1/projects", json=project_payload)
    assert project_resp.status_code == status.HTTP_201_CREATED
    project_id = project_resp.json()["id"]

    # Attempt to link a nonexistent task to the project
    link_resp = await test_api_client.post(f"/api/v1/tasks/99999/link-project/{project_id}")
    assert link_resp.status_code == status.HTTP_404_NOT_FOUND
    data = link_resp.json()
    assert "Task not found" in data["detail"]


@pytest.mark.asyncio
async def test_link_nonexistent_task_to_nonexistent_project_returns_404(test_api_client: AsyncClient) -> None:
    # Attempt to link a nonexistent task to a nonexistent project
    link_resp = await test_api_client.post("/api/v1/tasks/99999/link-project/99999")
    assert link_resp.status_code == status.HTTP_404_NOT_FOUND
    data = link_resp.json()
    assert "Task not found" in data["detail"] or "Project not found" in data["detail"]
