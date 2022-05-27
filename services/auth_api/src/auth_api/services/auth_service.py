from http.client import CONFLICT, BAD_REQUEST, FORBIDDEN

import pyotp
from sqlalchemy import or_

from auth_api.api.v1.schemas.user import UserSchema
from auth_api.commons.jwt_utils import create_tokens
from auth_api.commons.utils import get_device_type
from auth_api.exeptions import ServiceException
from auth_api.extensions import db, pwd_context
from auth_api.models.user import User, AuthHistory


class AuthService:

    def register_user(self, user_data: dict):
        """Регистрирует пользователя."""
        schema = UserSchema()
        user = schema.load(user_data)

        existing_user = User.query.filter(
            or_(User.username == user.username, User.email == user.email),
        ).first()
        if existing_user:
            raise ServiceException('Username or email is already taken!', http_code=CONFLICT)

        db.session.add(user)
        db.session.commit()

        return schema.dump(user)

    def get_tokens(self, username: str, password: str, totp_code: str = ''):
        """Возвращает пару токенов в обмен на учетные данные."""
        if not username or not password:
            raise ServiceException('Missing username or password.', http_code=BAD_REQUEST)

        user = User.query.filter_by(username=username).first()

        if user is None or not pwd_context.verify(password, user.password):
            raise ServiceException('Bad credentials.', http_code=BAD_REQUEST)

        if not user.is_active:
            raise ServiceException('Your account is blocked.', http_code=FORBIDDEN)

        if user.is_totp_enabled:
            secret = user.two_factor_secret
            totp = pyotp.TOTP(secret)

            if not totp.verify(totp_code):
                raise ServiceException('Wrong totp code.', http_code=BAD_REQUEST)

        access_token, refresh_token = create_tokens(user.uuid)
        return access_token, refresh_token

    def add_to_history(self, user_uuid: str, user_agent: str, ip_address: str):
        """Создает запись в истории входов."""
        db.session.add(
            AuthHistory(
                user_uuid=user_uuid,
                user_agent=user_agent,
                ip_address=ip_address,
                device=get_device_type(user_agent),
            ),
        )
        db.session.commit()
