from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class DateTimeValidatorMixin:
    """
    Mixin for Pydantic models to process 'deadline' field:
    If a timezone-aware datetime is provided, it's converted to UTC and then
    made timezone-naive.
    """

    @field_validator("deadline")
    @classmethod
    def remove_tzinfo(cls, value: Optional[datetime]) -> Optional[datetime]:
        """
        Validates and processes the 'deadline' field.
        Converts timezone-aware datetimes to UTC and removes timezone information.
        """
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value


class TaskBase(BaseModel, DateTimeValidatorMixin):
    """Base Pydantic schema for Task, defining common fields."""

    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    completed: bool = False
    project_id: Optional[int] = None


class TaskCreate(TaskBase):
    """Schema for creating a new Task."""

    pass


class TaskUpdate(BaseModel, DateTimeValidatorMixin):
    """Schema for updating an existing Task, making all fields optional."""

    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    completed: Optional[bool] = None
    project_id: Optional[int] = None


class Task(TaskBase):
    """Complete Task schema including 'id' and ORM compatibility."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class ProjectBase(BaseModel, DateTimeValidatorMixin):
    """Base Pydantic schema for Project, defining common fields."""

    title: str
    deadline: datetime


class ProjectCreate(ProjectBase):
    """Schema for creating a new Project."""

    pass


class ProjectUpdate(BaseModel, DateTimeValidatorMixin):
    """Schema for updating an existing Project, making all fields optional."""

    title: Optional[str] = None
    deadline: Optional[datetime] = None


class Project(ProjectBase):
    """Complete Project schema including 'id', tasks relationship, and ORM compatibility."""

    id: int
    tasks: list[Task] = []
    model_config = ConfigDict(from_attributes=True)
