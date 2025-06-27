from datetime import datetime

from fastapi import HTTPException, status


def check_deadline_consistency(
    task_deadline: datetime | None, project_deadline: datetime | None, task_id: int | None = None
) -> None:
    """
    Validate that a task's deadline does not exceed its project's deadline.

    Raises:
        HTTPException: If the task's deadline is later than the project's deadline.
    """
    if task_deadline and project_deadline and task_deadline > project_deadline:
        detail_message = "Task deadline cannot be later than project deadline."
        if task_id:
            detail_message = f"Task '{task_id}' has a deadline later than the project deadline."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_message,
        )
