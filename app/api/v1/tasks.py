from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models as models
import app.schemas as schemas
from app.database import get_db
from app.utils import check_deadline_consistency

router: APIRouter = APIRouter()


@router.get("", response_model=list[schemas.Task])
async def get_tasks(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> list[schemas.Task]:
    """
    Retrieve a list of all tasks with pagination.

    Returns:
        A list of tasks.
    """
    tasks = (await db.scalars(select(models.Task).offset(skip).limit(limit))).all()
    return [schemas.Task.model_validate(task) for task in tasks]


@router.get("/deadlines", response_model=list[schemas.Task])
async def get_tasks_with_deadlines(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> list[schemas.Task]:
    """
    Retrieve tasks that have a defined deadline, with pagination.

    Returns:
        A list of tasks with non-null deadlines.
    """
    query = select(models.Task).where(models.Task.deadline.is_not(None)).offset(skip).limit(limit)
    tasks = (await db.scalars(query)).all()
    return [schemas.Task.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=schemas.Task)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)) -> schemas.Task:
    """
    Retrieve a task by its ID.

    Raises:
        HTTPException: If the task does not exist.

    Returns:
        The requested task.
    """
    db_task = await db.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return schemas.Task.model_validate(db_task)


@router.post("", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
async def create_task(task_create: schemas.TaskCreate, db: AsyncSession = Depends(get_db)) -> schemas.Task:
    """
    Create a new task.

    If a project ID is provided, verifies that the project exists and the task's deadline does not exceed the project's deadline.

    Raises:
        HTTPException: If the project does not exist or the task's deadline is after the project's deadline.

    Returns:
        The created task.
    """
    if task_create.project_id:
        project = await db.get(models.Project, task_create.project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        check_deadline_consistency(task_create.deadline, project.deadline)

    new_task = models.Task(**task_create.model_dump())
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return schemas.Task.model_validate(new_task)


@router.put("/{task_id}", response_model=schemas.Task)
async def update_task(
    task_id: int, task_update: schemas.TaskUpdate, db: AsyncSession = Depends(get_db)
) -> schemas.Task:
    """
    Update an existing task by its ID.

    If the task is associated with a project, validates that the task's deadline does not exceed the project's deadline.

    Raises:
        HTTPException: If the task or associated project does not exist, or if the task's deadline is later than the project's deadline.

    Returns:
        The updated task.
    """
    db_task = await db.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    new_task_project_id: int | None = (
        task_update.project_id if task_update.project_id is not None else db_task.project_id
    )
    new_task_deadline: datetime | None = task_update.deadline if task_update.deadline is not None else db_task.deadline

    if new_task_project_id:
        project = await db.get(models.Project, new_task_project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        check_deadline_consistency(new_task_deadline, project.deadline)

    for field, value in task_update.model_dump(exclude_unset=True).items():
        setattr(db_task, field, value)
    await db.commit()
    await db.refresh(db_task)
    return schemas.Task.model_validate(db_task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """
    Delete a task by its ID.

    Raises:
        HTTPException: If the task with the given ID does not exist.

    Returns:
        None. Responds with HTTP 204 No Content on successful deletion.
    """
    db_task = await db.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await db.delete(db_task)
    await db.commit()


@router.post("/{task_id}/link-project/{project_id}", response_model=schemas.Task)
async def link_task_to_project(task_id: int, project_id: int, db: AsyncSession = Depends(get_db)) -> schemas.Task:
    """
    Link a task to a project.

    Associates the specified task with the given project. Validates that both the task and project exist,
    and that the task's deadline does not exceed the project's deadline.

    Raises:
        HTTPException: If the task or project does not exist, or if the task's deadline is later than the project's deadline.

    Returns:
        The updated task with the linked project.
    """
    db_task = await db.get(models.Task, task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db_project = await db.get(models.Project, project_id)
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    check_deadline_consistency(db_task.deadline, db_project.deadline)

    db_task.project_id = project_id
    await db.commit()
    await db.refresh(db_task)
    return schemas.Task.model_validate(db_task)
