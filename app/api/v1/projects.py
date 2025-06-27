from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models as models
import app.schemas as schemas
from app.database import get_db
from app.utils import check_deadline_consistency

router: APIRouter = APIRouter()


@router.get("", response_model=list[schemas.Project])
async def get_projects(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> list[schemas.Project]:
    """
    Retrieve a list of all projects with pagination.

    Returns:
        A list of projects.
    """
    projects = (await db.scalars(select(models.Project).offset(skip).limit(limit))).all()
    return [schemas.Project.model_validate(proj) for proj in projects]


@router.get("/{project_id}", response_model=schemas.Project)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)) -> schemas.Project:
    """
    Retrieve a project by its ID.

    Raises:
        HTTPException: If the project does not exist.

    Returns:
        The requested project.
    """
    db_project = await db.get(models.Project, project_id)
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return schemas.Project.model_validate(db_project)


@router.post("", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
async def create_project(project: schemas.ProjectCreate, db: AsyncSession = Depends(get_db)) -> schemas.Project:
    """
    Create a new project.

    Returns:
        The created project.
    """
    new_project = models.Project(**project.model_dump())
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return schemas.Project.model_validate(new_project)


@router.put("/{project_id}", response_model=schemas.Project)
async def update_project(
    project_id: int,
    project_update: schemas.ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> schemas.Project:
    """
    Update an existing project by its ID.

    If the project's deadline is updated, ensures it is not earlier than the deadline of any associated task.

    Raises:
        HTTPException: If the project does not exist, or if the updated deadline is earlier than any associated task's deadline.

    Returns:
        The updated project.
    """
    db_project = await db.get(models.Project, project_id)
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if project_update.deadline:
        for task in db_project.tasks:
            check_deadline_consistency(task.deadline, project_update.deadline, task_id=task.id)

    for field, value in project_update.model_dump(exclude_unset=True).items():
        setattr(db_project, field, value)

    await db.commit()
    await db.refresh(db_project)
    return schemas.Project.model_validate(db_project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """
    Delete a project by its ID.

    Raises:
        HTTPException: If the project does not exist.

    Returns:
        None. Responds with HTTP 204 No Content on successful deletion.
    """
    db_project = await db.get(models.Project, project_id)
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    await db.delete(db_project)
    await db.commit()


@router.get("/{project_id}/tasks", response_model=list[schemas.Task])
async def get_project_tasks(
    project_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> list[schemas.Task]:
    """
    Retrieve tasks associated with a specific project, with pagination.

    Raises:
        HTTPException: If the project with the given ID does not exist.

    Returns:
        A list of tasks linked to the specified project.
    """
    db_project = await db.get(models.Project, project_id)
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    query = select(models.Task).where(models.Task.project_id == project_id).offset(skip).limit(limit)
    tasks = (await db.scalars(query)).all()
    return [schemas.Task.model_validate(task) for task in tasks]
