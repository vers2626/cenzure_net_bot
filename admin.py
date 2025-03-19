from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from sqlalchemy import func
from datetime import datetime, timedelta

from config import settings
from database import get_db
from models import User, Subscription, Payment, Tariff

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in settings.ADMIN_IDS

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику бота"""
    if not is_admin(update.effective_user.id):
        return
    
    db = next(get_db())
    
    # Получаем статистику
    total_users = await db.query(func.count(User.id)).scalar()
    active_subscriptions = await db.query(func.count(Subscription.id)).filter(
        Subscription.is_active == True
    ).scalar()
    total_payments = await db.query(func.count(Payment.id)).scalar()
    total_revenue = await db.query(func.sum(Payment.amount)).filter(
        Payment.status == "completed"
    ).scalar() or 0
    
    await update.message.reply_text(
        f"📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Активных подписок: {active_subscriptions}\n"
        f"💰 Всего платежей: {total_payments}\n"
        f"💵 Общая выручка: {total_revenue}₽"
    )

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список пользователей"""
    if not is_admin(update.effective_user.id):
        return
    
    db = next(get_db())
    users = await db.query(User).all()
    
    if not users:
        await update.message.reply_text("Пользователей не найдено.")
        return
    
    message = "👥 Список пользователей:\n\n"
    for user in users:
        message += f"ID: {user.telegram_id}\n"
        message += f"Username: @{user.username or 'Нет'}\n"
        message += f"Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}\n"
        message += f"Активен: {'Да' if user.is_active else 'Нет'}\n"
        message += "-------------------\n"
    
    await update.message.reply_text(message)

async def admin_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление тарифами"""
    if not is_admin(update.effective_user.id):
        return
    
    db = next(get_db())
    tariffs = await db.query(Tariff).all()
    
    if not tariffs:
        await update.message.reply_text("Тарифов не найдено.")
        return
    
    keyboard = []
    for tariff in tariffs:
        keyboard.append([
            InlineKeyboardButton(
                f"{tariff.name} - {tariff.price}₽",
                callback_data=f"admin_tariff_{tariff.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("➕ Добавить тариф", callback_data="admin_add_tariff")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📋 Управление тарифами:",
        reply_markup=reply_markup
    )

async def admin_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список платежей"""
    if not is_admin(update.effective_user.id):
        return
    
    db = next(get_db())
    payments = await db.query(Payment).order_by(Payment.created_at.desc()).limit(10).all()
    
    if not payments:
        await update.message.reply_text("Платежей не найдено.")
        return
    
    message = "💰 Последние платежи:\n\n"
    for payment in payments:
        message += f"ID: {payment.payment_id}\n"
        message += f"Сумма: {payment.amount}{payment.currency}\n"
        message += f"Статус: {payment.status}\n"
        message += f"Дата: {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        message += "-------------------\n"
    
    await update.message.reply_text(message)

def setup_admin_handlers(application):
    """Добавляет обработчики админ-команд"""
    application.add_handler(CommandHandler("admin_stats", admin_stats))
    application.add_handler(CommandHandler("admin_users", admin_users))
    application.add_handler(CommandHandler("admin_tariffs", admin_tariffs))
    application.add_handler(CommandHandler("admin_payments", admin_payments)) 