from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.auth.users import current_active_user
from app.core.config import settings
from app.models.user import User

CurrentUser = Annotated[User, Depends(current_active_user)]


async def require_paid(user: CurrentUser) -> User:
    """D15: the gate exists now, the gateway lands in Phase 4."""
    if not settings.paywall_enabled:
        return user
    if user.paid_at is None:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail="Registration fee required.",
        )
    return user


PaidUser = Annotated[User, Depends(require_paid)]
