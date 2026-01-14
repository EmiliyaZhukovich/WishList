import logging
from email.message import EmailMessage
import smtplib

from redis import Redis
from rq import Queue, Retry
from rq.job import Job
from rq.exceptions import NoSuchJobError

import app.config as config

logger = logging.getLogger(__name__)

def get_redis_connection() -> Redis:
    return Redis.from_url(config.settings.redis_url)


def get_email_queue() -> Queue:
    return Queue(
        name="emails",
        connection=get_redis_connection(),
        default_timeout=120,
    )


def send_email_task(to: str, subject: str, body: str, from_email: str | None = None) -> str:
    """Задача для RQ worker-а"""
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    from_addr = (
        from_email
        or config.settings.smtp_from
        or config.settings.smtp_user
        or "noreply@yourapp.com"
    )
    msg["From"] = from_addr
    msg["To"] = to

    server = config.settings.smtp_server
    port = config.settings.smtp_port
    user = config.settings.smtp_user
    password = config.settings.smtp_password
    use_tls = config.settings.smtp_use_tls

    if not server or not port:
        logger.error("SMTP не сконфигурирован!")
        raise RuntimeError("SMTP конфигурация отсутствует")

    try:
        with smtplib.SMTP(server, port, timeout=30) as smtp:
            if use_tls:
                smtp.starttls()
            if user:
                smtp.login(user, password or "")
            smtp.send_message(msg)
        logger.info("Email успешно отправлен → %s (тема: %s)", to, subject)
        return "success"
    except Exception as e:
        logger.exception("Ошибка отправки email → %s", to)
        raise


def enqueue_welcome_email(to: str, wishlist_name: str) -> str | None:
    q = get_email_queue()

    try:
        job = q.enqueue(
            send_email_task,
            args=(to, "Ваш Вишлист создан успешно!", f"Вишлист '{wishlist_name}' создан."),
            retry=Retry(max=3, interval=[10, 30, 60]),
            result_ttl=3600 * 24,
            description=f"Welcome email to {to}",
        )
        logger.info("Задача на отправку email поставлена, job_id = %s", job.id)
        return job.id
    except Exception as e:
        logger.error("Не удалось поставить задачу на email → %s", str(e), exc_info=True)
        return None


def get_job_status(job_id: str) -> dict:
    try:
        job = Job.fetch(job_id, connection=get_redis_connection())
        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.return_value(),
            "exc_info": job.exc_info,
            "description": job.description,
        }
    except NoSuchJobError:
        return {"id": job_id, "status": "not_found"}
    except Exception as e:
        logger.warning("Ошибка при получении статуса job %s", job_id, exc_info=True)
        return {"id": job_id, "status": "error", "error": str(e)}