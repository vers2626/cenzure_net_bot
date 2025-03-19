from fastapi import FastAPI, Request
from datetime import datetime, timedelta
import hmac
import hashlib
import json

from config import settings
from database import get_db
from models import Payment, Subscription, User
from panel_api import PanelAPI

app = FastAPI()
panel_api = PanelAPI()

def verify_signature(request: Request, body: bytes) -> bool:
    """Проверка подписи вебхука"""
    signature = request.headers.get("X-Payment-Sha1-Hash")
    if not signature:
        return False
    
    expected_signature = hmac.new(
        settings.PAYMENT_TOKEN.encode(),
        body,
        hashlib.sha1
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@app.post("/webhook/payment/success")
async def payment_success(request: Request):
    """Обработчик успешного платежа"""
    body = await request.body()
    if not verify_signature(request, body):
        return {"status": "error", "message": "Invalid signature"}
    
    data = json.loads(body)
    payment_id = data.get("billId")
    
    if not payment_id:
        return {"status": "error", "message": "No payment ID"}
    
    db = next(get_db())
    payment = await db.query(Payment).filter(Payment.payment_id == payment_id).first()
    
    if not payment:
        return {"status": "error", "message": "Payment not found"}
    
    if payment.status == "completed":
        return {"status": "success", "message": "Payment already processed"}
    
    # Обновляем статус платежа
    payment.status = "completed"
    payment.completed_at = datetime.utcnow()
    
    # Создаем подписку
    user = await db.query(User).filter(User.id == payment.user_id).first()
    if not user:
        return {"status": "error", "message": "User not found"}
    
    # Создаем VPN-ключ
    inbound = await panel_api.create_inbound(
        email=f"user_{user.telegram_id}",
        days=30  # TODO: Получать из тарифа
    )
    
    if not inbound.get("success"):
        return {"status": "error", "message": "Failed to create VPN key"}
    
    subscription = Subscription(
        user_id=user.id,
        vpn_key=inbound["obj"]["id"],
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),  # TODO: Получать из тарифа
        is_active=True
    )
    
    db.add(subscription)
    await db.commit()
    
    return {"status": "success", "message": "Payment processed"}

@app.post("/webhook/payment/fail")
async def payment_fail(request: Request):
    """Обработчик неуспешного платежа"""
    body = await request.body()
    if not verify_signature(request, body):
        return {"status": "error", "message": "Invalid signature"}
    
    data = json.loads(body)
    payment_id = data.get("billId")
    
    if not payment_id:
        return {"status": "error", "message": "No payment ID"}
    
    db = next(get_db())
    payment = await db.query(Payment).filter(Payment.payment_id == payment_id).first()
    
    if not payment:
        return {"status": "error", "message": "Payment not found"}
    
    # Обновляем статус платежа
    payment.status = "failed"
    
    await db.commit()
    
    return {"status": "success", "message": "Payment marked as failed"} 