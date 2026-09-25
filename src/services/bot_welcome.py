"""Welcome replies to authenticated MAX start events."""

from maxapi.enums.chat_type import ChatType
from maxapi.types import BotStarted, MessageCreated
from maxapi.types.attachments.attachment import ButtonsPayload
from maxapi.types.attachments.buttons import OpenAppButton

from src.config import Settings
from src.errors import ServiceError
from src.services.max_bot import max_bot

WELCOME_TEXT = (
    "Привет! Это «Рядом» — ваш помощник для поездок на выходные 🧳\n\n"
    "Выберите готовый маршрут или расскажите о своих планах — поможем собрать "
    "поездку с учётом интересов, бюджета и погоды. Все маршруты сохранятся "
    "в разделе «Мои поездки».\n\n"
    "Нажмите кнопку ниже, чтобы открыть приложение и начать путешествие."
)


def welcome_keyboard(username: str):
    return ButtonsPayload(
        buttons=[[OpenAppButton(text="Открыть приложение", web_app=username)]]
    ).pack()


def welcome_recipient(update: dict, username: str) -> int | None:
    """SDK parses events; our rule only responds to starts in private dialogs."""
    kind = update.get("update_type")
    if kind == "bot_started":
        event = BotStarted.model_validate(update)
        user = event.user
        if event.timestamp < 0:
            return None
    elif kind == "message_created":
        event = MessageCreated.model_validate(update)
        message = event.message
        user = message.sender
        if not user or message.recipient.chat_type != ChatType.DIALOG:
            return None

        words = (message.body.text or "").split()
        if not words or words[0].lower() not in {
            "/start",
            f"/start@{username.lower()}",
        }:
            return None

        if not message.body.mid:
            return None
    else:
        return None

    if user.is_bot or user.user_id <= 0:
        return None

    return user.user_id


async def send_welcome(settings: Settings, user_id: int) -> None:
    async with max_bot(settings) as bot:
        result = await bot.send_message(
            user_id=user_id,
            text=WELCOME_TEXT,
            attachments=[welcome_keyboard(settings.max_bot_username)],
        )

        if not result or not result.message.body.mid:
            raise ServiceError(
                "max", "Не удалось отправить приветствие", status_code=503
            )


async def handle_welcome(update: dict, settings: Settings) -> None:
    user_id = welcome_recipient(update, settings.max_bot_username)
    if user_id is not None:
        await send_welcome(settings, user_id)
