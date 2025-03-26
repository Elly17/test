from telethon import TelegramClient
import json
import asyncio
import logging

# Настройка логирования
logger = logging.getLogger('telegram_notify')

async def send_telegram_notification(api_id, api_hash, session_name, channel_id, topic_id, message):
    """Отправляет сообщение в топик канала Telegram"""
    try:
        # Инициализация клиента
        client = TelegramClient(session_name, api_id, api_hash)
        await client.start()
        
        # Отправка сообщения в топик канала
        await client.send_message(
            entity=channel_id,
            message=message,
            reply_to=topic_id  # ID топика
        )
        
        await client.disconnect()
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке в Telegram: {str(e)}")
        return False

def handle(data):
    """
    Функция обработки запроса на помощь менеджера
    Отправляет уведомление в Telegram канал
    
    Ожидаемые параметры в data:
    - user_id: ID пользователя (опционально)
    - user_name: Имя пользователя (опционально)  
    - user_contact: Контакт пользователя (опционально)
    - telegram_api_id: API ID для Telegram
    - telegram_api_hash: API Hash для Telegram
    - telegram_session: Имя сессии
    - telegram_channel_id: ID канала
    - telegram_topic_id: ID топика в канале
    - custom_message: Кастомное сообщение (опционально)
    """
    try:
        # Получаем параметры из данных
        user_id = data.get('user_id', 'Неизвестный ID')
        user_name = data.get('user_name', 'Неизвестный пользователь')
        user_contact = data.get('user_contact', 'Не указан')
        
        # Параметры для подключения к Telegram
        telegram_api_id = int(data.get('telegram_api_id', 0))
        telegram_api_hash = data.get('telegram_api_hash', '')
        telegram_session = data.get('telegram_session', 'salebot_session')
        telegram_channel_id = data.get('telegram_channel_id', '')
        telegram_topic_id = int(data.get('telegram_topic_id', 0))
        
        # Кастомное сообщение или формируем стандартное
        custom_message = data.get('custom_message', '')
        
        if not custom_message:
            message = f"⚠️ ТРЕБУЕТСЯ ПОМОЩЬ МЕНЕДЖЕРА ⚠️\n\n" \
                    f"👤 Пользователь: {user_name}\n" \
                    f"🆔 ID: {user_id}\n" \
                    f"📱 Контакт: {user_contact}\n\n" \
                    f"Пожалуйста, свяжитесь с пользователем как можно скорее!"
        else:
            message = custom_message
        
        # Проверка обязательных параметров
        if not telegram_api_id or not telegram_api_hash or not telegram_channel_id:
            return {
                "success": False,
                "error": "Отсутствуют обязательные параметры для Telegram API"
            }
        
        # Создаем новый event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Отправляем уведомление
        result = loop.run_until_complete(
            send_telegram_notification(
                telegram_api_id,
                telegram_api_hash,
                telegram_session,
                telegram_channel_id,
                telegram_topic_id,
                message
            )
        )
        
        # Закрываем loop
        loop.close()
        
        if result:
            return {
                "success": True,
                "message": "Уведомление успешно отправлено в Telegram",
                "user_name": user_name,
                "user_id": user_id
            }
        else:
            return {
                "success": False,
                "error": "Не удалось отправить уведомление"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
