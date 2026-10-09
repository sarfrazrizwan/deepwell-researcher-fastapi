import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, InvalidPasswordException, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_async_session
from app.models.user import User
from app.schema.user import UserCreate
from sqlalchemy import select


logger = logging.getLogger(__name__)


async def get_user_db(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.reset_password_secret
    verification_token_secret = settings.verification_secret

    async def validate_password(
        self, password: str, user: UserCreate | User
    ) -> None:
        if len(password) < 12:
            raise InvalidPasswordException("Password must be at least 12 characters.")
        if user.email.lower() in password.lower():
            raise InvalidPasswordException("Password must not contain your email.")

    async def on_after_register(
        self, user: User, request: Request | None = None
    ) -> None:
        logger.info("user registered: %s", user.id)
        

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        logger.info("password reset requested for %s, token=%s", user.id, token)
        # Phase 4: send email. Logging the token is dev-only.


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase, Depends(get_user_db)],
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)
