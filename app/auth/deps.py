from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.auth.users import current_active_user
from app.config import settings
from app.models.user import User

CurrentUser = Annotated[User, Depends(current_active_user)]
