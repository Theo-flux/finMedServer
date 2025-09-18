import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import jwt
from fastapi import Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from jwt import ExpiredSignatureError, PyJWTError
from passlib.context import CryptContext

from src.config import Config
from src.db.redis import redis_client
from src.utils.exceptions import ExpiredLink, InvalidLink, InvalidToken, RefreshTokenExpired, TokenExpired

from .schemas import TokenUserModel


class Authentication:
    password_context = CryptContext(schemes=["bcrypt"])
    ACCESS_TOKEN_EXPIRY_IN_SECONDS = 900  # 15 mins
    REFRESH_TOKEN_EXPIRY_IN_SECONDS = 604800  # 7 days

    PWD_RESET_TOKEN_EXPIRY_IN_SECONDS = 3600  # 1 hour
    serializer: URLSafeTimedSerializer = URLSafeTimedSerializer(secret_key=Config.JWT_SECRET, salt=Config.EMAIL_SALT)

    @staticmethod
    def generate_password_hash(password: str) -> str:
        return Authentication.password_context.hash(password)

    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        return Authentication.password_context.verify(password, hash)

    @staticmethod
    async def create_token(
        user_data: TokenUserModel,
        response: Optional[Response] = None,
        expiry: timedelta = None,
        refresh: bool = False,
    ) -> str:
        payload = {}

        if refresh:
            payload["user"] = user_data.model_dump(mode="json", include={"uid", "id"})
        else:
            payload["user"] = user_data.model_dump(mode="json")

        payload["exp"] = int(
            (
                datetime.now()
                + (
                    expiry
                    if expiry is not None
                    else timedelta(
                        seconds=(
                            Authentication.REFRESH_TOKEN_EXPIRY_IN_SECONDS
                            if refresh
                            else Authentication.ACCESS_TOKEN_EXPIRY_IN_SECONDS
                        )
                    )
                )
            ).timestamp()
        )
        payload["jti"] = str(uuid4())
        payload["refresh"] = refresh
        token = jwt.encode(payload=payload, key=Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

        if refresh:
            try:
                redis_key = payload["jti"]
                await redis_client.client.set(
                    name=redis_key, value=token, ex=Authentication.REFRESH_TOKEN_EXPIRY_IN_SECONDS
                )

                if response:
                    response.set_cookie(
                        key="refresh_token",
                        value=redis_key,
                        httponly=True,
                        samesite="none",
                        secure=True,
                        max_age=Authentication.REFRESH_TOKEN_EXPIRY_IN_SECONDS,
                        path="/",
                        domain="localhost",
                    )

            except Exception as e:
                logging.error(f"Failed to initialize Redis client: {e}")
                pass

        return token

    @staticmethod
    async def decode_token(token: str):
        try:
            token_payload = jwt.decode(
                jwt=token,
                key=Config.JWT_SECRET,
                algorithms=[Config.JWT_ALGORITHM],
                verify=True,
            )
            return token_payload
        except ExpiredSignatureError:
            try:
                unverified_payload = jwt.decode(
                    jwt=token, key=Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM], options={"verify_exp": False}
                )
                is_refresh = unverified_payload.get("refresh", False)
                logging.warning(f"Token expired. Is refresh: {is_refresh}")

                if is_refresh:
                    logging.warning("Raising RefreshTokenExpired")
                    raise RefreshTokenExpired()
                else:
                    logging.warning("Raising TokenExpired")
                    raise TokenExpired()

            except (KeyError, ValueError, TypeError) as decode_error:
                logging.warning(f"Could not decode expired token payload: {decode_error}")
                raise TokenExpired()
            except RefreshTokenExpired:
                raise
            except TokenExpired:
                raise
        except PyJWTError:
            logging.exception("JWT decoding failed.")
            raise InvalidToken()

    @staticmethod
    def create_url_safe_token(data: dict):
        return Authentication.serializer.dumps(data)

    @staticmethod
    def decode_url_safe_token(token: str):
        try:
            return Authentication.serializer.loads(token, max_age=Authentication.PWD_RESET_TOKEN_EXPIRY_IN_SECONDS)
        except SignatureExpired:
            logging.error("Token expired")
            raise ExpiredLink()
        except BadSignature:
            logging.error("Invalid token")
            raise InvalidLink()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise InvalidLink()
