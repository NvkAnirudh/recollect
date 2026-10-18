from fastapi import APIRouter
from pydantic import BaseModel

from recollect.core.security import AuthenticatedUser

router = APIRouter(tags=["me"])


class MeResponse(BaseModel):
    id: str
    email: str | None


@router.get("/me")
async def read_me(user: AuthenticatedUser) -> MeResponse:
    """The authenticated caller. Lets the web app confirm its session works."""
    return MeResponse(id=str(user.id), email=user.email)
