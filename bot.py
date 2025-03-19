import logging
from datetime import datetime, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

from config import settings
from database import get_db
from models import User, Subscription, Payment, Tariff
from panel_api import PanelAPI
from payment import PaymentSystem

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CHOOSING_TARIFF, CONFIRMING_PAYMENT = range(2)

# Инициализация API и платежной системы
panel_api = PanelAPI()
payment_system = PaymentSystem()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    db = next(get_db())
    
    # Проверяем, существует ли пользователь
    db_user = await db.query(User).filter(User.telegram_id == user.id).first()
    if not db_user:
        # Создаем нового пользователя
        db_user = User(
            telegram_id=user.id,
            username=user.username
        )
        db.add(db_user)
        await db.commit()
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я бот для управления VPN-подпиской. Вот что я умею:\n\n"
        "/buy - Купить подписку\n"
        "/status - Проверить статус подписки\n"
        "/help - Показать это сообщение"
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /buy"""
    db = next(get_db())
    
    # Получаем доступные тарифы
    tariffs = await db.query(Tariff).filter(Tariff.is_active == True).all()
    
    if not tariffs:
        await update.message.reply_text("К сожалению, сейчас нет доступных тарифов.")
        return
    
    # Создаем клавиатуру с тарифами
    keyboard = []
    for tariff in tariffs:
        keyboard.append([
            InlineKeyboardButton(
                f"{tariff.name} - {tariff.price}₽",
                callback_data=f"tariff_{tariff.id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите тарифный план:",
        reply_markup=reply_markup
    )
    
    return CHOOSING_TARIFF

async def tariff_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора тарифа"""
    query = update.callback_query
    await query.answer()
    
    tariff_id = int(query.data.split('_')[1])
    db = next(get_db())
    tariff = await db.query(Tariff).filter(Tariff.id == tariff_id).first()
    
    if not tariff:
        await query.edit_message_text("Ошибка: тариф не найден.")
        return ConversationHandler.END
    
    # Создаем платеж
    payment_id = f"vpn_{query.from_user.id}_{datetime.now().timestamp()}"
    payment = await payment_system.create_payment(
        amount=tariff.price,
        currency="RUB",
        payment_id=payment_id
    )
    
    if not payment.get("payUrl"):
        await query.edit_message_text("Ошибка при создании платежа. Попробуйте позже.")
        return ConversationHandler.END
    
    # Сохраняем информацию о платеже
    db_payment = Payment(
        user_id=query.from_user.id,
        amount=tariff.price,
        currency="RUB",
        payment_id=payment_id,
        status="pending"
    )
    db.add(db_payment)
    await db.commit()
    
    # Создаем клавиатуру с кнопкой оплаты
    keyboard = [[InlineKeyboardButton("Оплатить", url=payment["payUrl"])]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"Вы выбрали тариф: {tariff.name}\n"
        f"Стоимость: {tariff.price}₽\n"
        f"Длительность: {tariff.duration_days} дней\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=reply_markup
    )
    
    return CONFIRMING_PAYMENT

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    db = next(get_db())
    user = await db.query(User).filter(User.telegram_id == update.effective_user.id).first()
    
    if not user:
        await update.message.reply_text("Пожалуйста, начните с команды /start")
        return
    
    # Получаем активную подписку
    subscription = await db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.is_active == True
    ).first()
    
    if not subscription:
        await update.message.reply_text(
            "У вас нет активной подписки.\n"
            "Используйте команду /buy для покупки."
        )
        return
    
    # Получаем информацию о ключе
    inbound = await panel_api.get_inbound(subscription.vpn_key)
    
    if not inbound.get("success"):
        await update.message.reply_text("Ошибка при получении информации о ключе.")
        return
    
    await update.message.reply_text(
        f"Статус вашей подписки:\n"
        f"Действует до: {subscription.end_date.strftime('%d.%m.%Y')}\n"
        f"Трафик: ↑{inbound['obj']['up']}MB ↓{inbound['obj']['down']}MB"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/buy - Купить подписку\n"
        "/status - Проверить статус подписки\n"
        "/help - Показать это сообщение"
    )

def main():
    """Запуск бота"""
    application = Application.builder().token(settings.BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    
    # Добавляем ConversationHandler для процесса покупки
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("buy", buy)],
        states={
            CHOOSING_TARIFF: [
                CallbackQueryHandler(tariff_chosen, pattern="^tariff_")
            ],
            CONFIRMING_PAYMENT: [
                CallbackQueryHandler(tariff_chosen, pattern="^tariff_")
            ]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(conv_handler)
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main() 