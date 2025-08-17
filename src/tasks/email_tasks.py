import asyncio

from src.tasks import celery_app
from src.utils.mail import Mailer


@celery_app.task(name="send_email_verification_task", bind=True, max_retries=3, default_retry_delay=5)
def send_email_verification_task(*args, **kwargs):
    email = kwargs.get("email") or args[0]
    first_name = kwargs.get("first_name") or args[1]
    base_url = kwargs.get("base_url") or args[2]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(Mailer.send_email_verification(email=email, first_name=first_name, base_url=base_url))
    finally:
        loop.close()


@celery_app.task(name="send_password_reset_task", bind=True, max_retries=3, default_retry_delay=5)
def send_password_reset_task(*args, **kwargs):
    email = kwargs.get("email") or args[0]
    first_name = kwargs.get("first_name") or args[1]
    base_url = kwargs.get("base_url") or args[2]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(Mailer.send_password_reset(email=email, first_name=first_name, base_url=base_url))
    finally:
        loop.close()
