from fastapi import APIRouter

router: APIRouter = APIRouter()


@router.get("", response_model=dict[str, str])
async def health() -> dict[str, str]:
    """
    Health check endpoint.

    Returns a simple status message indicating that the service is running.

    Returns:
        A dictionary with a status message.
    """
    return {"status": "OK"}
