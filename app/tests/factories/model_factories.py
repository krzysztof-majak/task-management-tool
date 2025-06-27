from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, cast

from factory import Faker, LazyFunction, Sequence, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Task


class BaseModelFactory(SQLAlchemyModelFactory):  # type: ignore[type-arg]
    class Meta:
        abstract = True
        sqlalchemy_session = None
        sqlalchemy_session_persistence = None

    @classmethod
    def bind_session(cls, session: AsyncSession) -> None:
        cast(Any, cls._meta).sqlalchemy_session = session


class ProjectFactory(BaseModelFactory):
    class Meta:
        model = Project

    id: ClassVar[int] = Sequence(lambda n: n + 1)  # type: ignore[assignment]
    title: ClassVar[str] = Faker("sentence", nb_words=3)  # type: ignore[assignment]
    deadline: ClassVar[datetime] = LazyFunction(
        lambda: (datetime.now(timezone.utc) + timedelta(days=30)).replace(tzinfo=None)
    )  # type: ignore[assignment]


class TaskFactory(BaseModelFactory):
    class Meta:
        model = Task

    id: ClassVar[int] = Sequence(lambda n: n + 1)  # type: ignore[assignment]
    title: ClassVar[str] = Faker("sentence", nb_words=4)  # type: ignore[assignment]
    description: ClassVar[str] = Faker("paragraph")  # type: ignore[assignment]
    deadline: ClassVar[datetime] = LazyFunction(
        lambda: (datetime.now(timezone.utc) + timedelta(days=15)).replace(tzinfo=None)
    )  # type: ignore[assignment]
    completed: ClassVar[bool] = Faker("pybool")  # type: ignore[assignment]
    project: ClassVar[Project] = SubFactory(ProjectFactory)  # type: ignore[assignment]
