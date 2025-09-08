import logging
from datetime import datetime, timedelta
from uuid import uuid4

import jwt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from jwt import ExpiredSignatureError, PyJWTError
from passlib.context import CryptContext

from src.config import Config
from src.utils.exceptions import ExpiredLink, InvalidLink, InvalidToken, RefreshTokenExpired, TokenExpired

from .schemas import TokenUserModel


class Authentication:
    password_context = CryptContext(schemes=["bcrypt"])
    # ACCESS_TOKEN_EXPIRY = 2700  # 45mins
    # REFRESH_TOKEN_EXPIRY = 5184000  # 60days

    ACCESS_TOKEN_EXPIRY = 60  # 1 minutes
    REFRESH_TOKEN_EXPIRY = 150  # 2.5 minutes
    PWD_RESET_TOKEN_EXPIRY = 3600
    serializer: URLSafeTimedSerializer = URLSafeTimedSerializer(secret_key=Config.JWT_SECRET, salt=Config.EMAIL_SALT)

    @staticmethod
    def generate_password_hash(password: str) -> str:
        return Authentication.password_context.hash(password)

    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        return Authentication.password_context.verify(password, hash)

    @staticmethod
    def create_token(user_data: TokenUserModel, expiry: timedelta = None, refresh: bool = False):
        payload = {}

        payload["user"] = user_data.model_dump(mode="json")
        payload["exp"] = int(
            (
                datetime.now()
                + (
                    expiry
                    if expiry is not None
                    else timedelta(
                        seconds=Authentication.REFRESH_TOKEN_EXPIRY if refresh else Authentication.ACCESS_TOKEN_EXPIRY
                    )
                )
            ).timestamp()
        )
        payload["jti"] = str(uuid4())
        payload["refresh"] = refresh
        token = jwt.encode(payload=payload, key=Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

        return token

    @staticmethod
    def decode_token(token: str):
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
                    jwt=token,
                    key=Config.JWT_SECRET,
                    algorithms=[Config.JWT_ALGORITHM],
                    options={"verify_signature": False, "verify_exp": False, "verify_aud": False, "verify_iss": False},
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
            return Authentication.serializer.loads(token, max_age=Authentication.PWD_RESET_TOKEN_EXPIRY)
        except SignatureExpired:
            logging.error("Token expired")
            raise ExpiredLink()
        except BadSignature:
            logging.error("Invalid token")
            raise InvalidLink()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise InvalidLink()
