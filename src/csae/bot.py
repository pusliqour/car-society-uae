import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from .approval import ApprovalError, ApprovalService
from .github_store import DuplicateEvent, GitHubEventStore, GitHubStoreError
from .ingest import InvalidSubmission


FORMAT = """Send one Instagram link with labeled details:

Club: Dubai Night Riders
Event: Mountain Drive
Date: 2026-11-14
Time: 20:00
Type: Drive
Emirate: Dubai
Location: Last Exit
Details: Meet 19:30, depart 20:00"""


def allowed_chats():
    raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "")
    try:
        values = {int(value.strip()) for value in raw.split(",") if value.strip()}
    except ValueError as exc:
        raise RuntimeError("TELEGRAM_ALLOWED_CHAT_IDS must contain numeric chat IDs") from exc
    if not values:
        raise RuntimeError("TELEGRAM_ALLOWED_CHAT_IDS must contain at least one chat ID")
    return values


def build_service():
    store = GitHubEventStore(
        os.environ.get("GITHUB_OWNER", "pusliqour"),
        os.environ.get("GITHUB_REPO", "car-society-uae"),
        lambda: os.environ.get("GITHUB_TOKEN", ""),
        branch=os.environ.get("GITHUB_BRANCH", "main"),
    )
    return ApprovalService(store)


async def format_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_message and update.effective_chat.id in context.bot_data["allowed"]:
        await update.effective_message.reply_text(FORMAT)


async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    if not chat or not message or chat.id not in context.bot_data["allowed"]:
        return
    text = message.text or message.caption or ""
    try:
        pending = context.bot_data["service"].submit(chat.id, text)
    except InvalidSubmission as exc:
        await message.reply_text(f"Could not prepare this event: {exc}\n\n{FORMAT}")
        return
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve & publish", callback_data=f"approve:{pending.token}"),
        InlineKeyboardButton("✖ Reject", callback_data=f"reject:{pending.token}"),
    ]])
    await message.reply_text("Review before publishing:\n\n" + pending.preview, reply_markup=keyboard)


async def decide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat = update.effective_chat
    if not query or not chat or chat.id not in context.bot_data["allowed"]:
        return
    await query.answer()
    action, _, token = (query.data or "").partition(":")
    try:
        if action == "reject":
            context.bot_data["service"].reject(chat.id, token)
            await query.edit_message_text("Rejected. Nothing was published.")
            return
        if action != "approve":
            raise ApprovalError("Unknown approval action.")
        result = context.bot_data["service"].approve(chat.id, token)
        text = "Published to the CSAE calendar through GitHub."
        if result.get("commit_url"):
            text += "\n" + result["commit_url"]
        await query.edit_message_text(text)
    except DuplicateEvent as exc:
        await query.edit_message_text(f"Not published: {exc}")
    except (ApprovalError, GitHubStoreError) as exc:
        await query.edit_message_text(f"Could not publish: {exc}")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    application = Application.builder().token(token).build()
    application.bot_data["allowed"] = allowed_chats()
    application.bot_data["service"] = build_service()
    application.add_handler(CommandHandler(["start", "format"], format_help))
    application.add_handler(CallbackQueryHandler(decide, pattern=r"^(approve|reject):"))
    application.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, receive))
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)


if __name__ == "__main__":
    main()
