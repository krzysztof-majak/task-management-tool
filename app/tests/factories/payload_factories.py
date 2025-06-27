from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, Dict, Generic, TypeVar

from factory import Factory, Faker, LazyFunction
from pydantic import BaseModel

from app.schemas import ProjectCreate, TaskCreate
from app.tests.utils import convert_datetimes

ModelType = TypeVar("ModelType", bound=BaseModel)


class BasePayloadFactory(Factory[ModelType], Generic[ModelType]):
    @classmethod
    def as_dict(cls, **overrides: Any) -> Dict[str, Any]:
        instance = cls.build(**overrides)
        data = instance.model_dump()
        return convert_datetimes(data)


class ProjectPayloadFactory(BasePayloadFactory[ProjectCreate]):
    class Meta:
        model = ProjectCreate

    title: ClassVar[str] = Faker("sentence", nb_words=3)  # type: ignore[assignment]
    deadline: ClassVar[datetime] = LazyFunction(lambda: (datetime.now(timezone.utc) + timedelta(days=30)))  # type: ignore[assignment]


class TaskPayloadFactory(BasePayloadFactory[TaskCreate]):
    class Meta:
        model = TaskCreate

    title: ClassVar[str] = Faker("sentence", nb_words=4)  # type: ignore[assignment]
    description: ClassVar[str] = Faker("paragraph")  # type: ignore[assignment]
    deadline: ClassVar[datetime] = LazyFunction(lambda: (datetime.now(timezone.utc) + timedelta(days=15)))  # type: ignore[assignment]
    completed: ClassVar[bool] = False
    project_id: ClassVar[int | None] = None
