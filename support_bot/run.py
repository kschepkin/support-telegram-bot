import peewee
import telegram
import datetime
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from db_connector import (dbhandle, Messages, BannedUsers, create_message_in_db, get_message_id_from_db,
                          set_last_reply_time, set_new_banned_user, remove_message_from_db,
                          get_banned_users,
                          is_not_to_many_messages_in_period, get_chat_id_by_full_name_and_date)
from settings import ADMIN_CHAT_ID, BAN_MESSAGE, MESSAGE_IS_RECEIVED_BY_ADMIN, START_MESSAGE, BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def get_origin_message_chat_id(forward_origin_message):
    """Получает ID чата из forward_origin сообщения"""
    try:
        if forward_origin_message['type'] == telegram.constants.MessageOriginType.USER:
            return forward_origin_message['sender_user']['id']
        if forward_origin_message['type'] == telegram.constants.MessageOriginType.HIDDEN_USER:
            user_full_name = forward_origin_message['sender_user_name']
            date_of_sending = forward_origin_message['date']
            return get_chat_id_by_full_name_and_date(user_full_name, date_of_sending)
    except KeyError as e:
        logger.error(f"Ошибка при получении chat_id из forward_origin: {e}")
        return None


def get_user_full_name_by_origin_message(forward_origin_message):
    """Получает полное имя пользователя из forward_origin сообщения"""
    try:
        if forward_origin_message['type'] == telegram.constants.MessageOriginType.USER:
            first_name = forward_origin_message["sender_user"].get("first_name", "")
            last_name = forward_origin_message["sender_user"].get("last_name", "")
            return f'{first_name} {last_name}'.strip()
        if forward_origin_message['type'] == telegram.constants.MessageOriginType.HIDDEN_USER:
            return forward_origin_message['sender_user_name']
    except KeyError as e:
        logger.error(f"Ошибка при получении имени пользователя из forward_origin: {e}")
        return "Неизвестный пользователь"


def get_user_nickname_by_origin_message(forward_origin_message):
    """Получает никнейм пользователя из forward_origin сообщения"""
    try:
        if forward_origin_message['type'] == telegram.constants.MessageOriginType.USER:
            return forward_origin_message['sender_user'].get('username')
        else:
            return None
    except KeyError as e:
        logger.error(f"Ошибка при получении никнейма из forward_origin: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        await context.bot.send_message(chat_id=update.message.chat_id, text=START_MESSAGE)
        logger.info(f"Отправлено приветственное сообщение пользователю {update.message.chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке приветственного сообщения: {e}")


async def forward_message_to_admin_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик сообщений - пересылает сообщения между пользователями и админами"""
    try:
        if update.message.chat_id == ADMIN_CHAT_ID:
            # Обработка сообщений от админов
            await handle_admin_message(update, context)
        else:
            # Обработка сообщений от пользователей
            await handle_user_message(update, context)
    except Exception as e:
        logger.error(f"Общая ошибка в forward_message_to_admin_group: {e}")
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID if update.message.chat_id != ADMIN_CHAT_ID else update.message.chat_id,
                text=f"Произошла ошибка при обработке сообщения: {str(e)}"
            )
        except Exception as send_error:
            logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений от администраторов"""
    # Проверяем, что сообщение является ответом на пересланное сообщение
    if not update.message.reply_to_message:
        logger.warning("Админ отправил сообщение не в ответ на пересланное сообщение")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text="Для ответа пользователю, отвечайте на его пересланное сообщение"
        )
        return

    # Проверяем, что reply_to_message имеет forward_origin
    if not hasattr(update.message.reply_to_message, 'forward_origin') or not update.message.reply_to_message.forward_origin:
        logger.warning("Сообщение не содержит информации о пересылке")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text="Это сообщение не является пересланным от пользователя"
        )
        return

    try:
        forward_origin_message = update.message.reply_to_message.forward_origin.to_dict()
        origin_message_chat_id = get_origin_message_chat_id(forward_origin_message)
        
        if not origin_message_chat_id:
            logger.error("Не удалось определить chat_id отправителя")
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text="Не удалось определить получателя сообщения"
            )
            return

        # Обработка команды бана
        if update.message.text == BAN_MESSAGE:
            await handle_ban_command(update, context, forward_origin_message, origin_message_chat_id)
        else:
            # Отправка ответа пользователю
            await send_reply_to_user(update, context, forward_origin_message, origin_message_chat_id)
            
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от админа: {e}")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Ошибка при обработке сообщения: {str(e)}"
        )


async def handle_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           forward_origin_message: dict, origin_message_chat_id: int):
    """Обработка команды бана пользователя"""
    try:
        origin_message_user_nickname = get_user_nickname_by_origin_message(forward_origin_message)
        origin_message_user_full_name = get_user_full_name_by_origin_message(forward_origin_message)
        
        set_new_banned_user(origin_message_chat_id, origin_message_user_nickname, origin_message_user_full_name)
        remove_message_from_db(update.message.from_user.id)
        
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Пользователь {origin_message_user_full_name} (ID: {origin_message_chat_id}) заблокирован"
        )
        logger.info(f"Пользователь {origin_message_chat_id} заблокирован")
        
    except Exception as e:
        logger.error(f"Ошибка при блокировке пользователя: {e}")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Ошибка при блокировке пользователя: {str(e)}"
        )


async def send_reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           forward_origin_message: dict, origin_message_chat_id: int):
    """Отправка ответа пользователю"""
    try:
        origin_message_timestamp = forward_origin_message['date']
        
        # Получаем ID оригинального сообщения из БД
        original_message_id = get_message_id_from_db(origin_message_chat_id, origin_message_timestamp)
        
        reply_parameters = None
        if original_message_id:
            reply_parameters = telegram.ReplyParameters(
                message_id=original_message_id,
                chat_id=origin_message_chat_id
            )

        # Отправляем соответствующий тип сообщения
        success = await send_message_by_type(update, context, origin_message_chat_id, reply_parameters)
        
        if success:
            # Обновляем время последнего ответа
            set_last_reply_time(
                user_id=origin_message_chat_id, 
                message_date=origin_message_timestamp,
                last_reply_time=datetime.datetime.now().timestamp()
            )
            logger.info(f"Ответ отправлен пользователю {origin_message_chat_id}")
        else:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID, 
                text='Сообщение не доставлено. Неподдерживаемый формат сообщения'
            )
            
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа пользователю: {e}")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Ошибка при отправке ответа: {str(e)}"
        )


async def send_message_by_type(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              chat_id: int, reply_parameters) -> bool:
    """Отправляет сообщение соответствующего типа"""
    try:
        message = update.message
        
        if message.text is not None:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message.text,
                reply_parameters=reply_parameters
            )
        elif message.document is not None:
            await context.bot.send_document(
                chat_id=chat_id,
                document=message.document.file_id,
                caption=message.caption,
                reply_parameters=reply_parameters
            )
        elif message.audio is not None:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=message.audio.file_id,
                caption=message.caption,
                reply_parameters=reply_parameters
            )
        elif message.video is not None:
            await context.bot.send_video(
                chat_id=chat_id,
                video=message.video.file_id,
                caption=message.caption,
                reply_parameters=reply_parameters
            )
        elif message.animation is not None:
            await context.bot.send_animation(
                chat_id=chat_id,
                animation=message.animation.file_id,
                caption=message.caption,
                reply_parameters=reply_parameters
            )
        elif message.photo and len(message.photo) > 0:
            # Берем фото с наибольшим разрешением (последнее в списке)
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=message.photo[-1].file_id,
                caption=message.caption,
                reply_parameters=reply_parameters
            )
        elif message.sticker is not None:
            await context.bot.send_sticker(
                chat_id=chat_id,
                sticker=message.sticker.file_id,
                reply_parameters=reply_parameters
            )
        elif message.voice is not None:
            await context.bot.send_voice(
                chat_id=chat_id,
                voice=message.voice.file_id,
                caption=message.caption,
                reply_parameters=reply_parameters
            )
        else:
            return False  # Неподдерживаемый тип сообщения
            
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения типа {type(update.message)}: {e}")
        return False


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений от пользователей"""
    try:
        user_id = update.message.from_user.id
        
        # Проверяем, не заблокирован ли пользователь
        if user_id in get_banned_users():
            await context.bot.send_message(
                chat_id=update.message.chat_id, 
                text=MESSAGE_IS_RECEIVED_BY_ADMIN
            )
            logger.info(f"Заблокированный пользователь {user_id} попытался отправить сообщение")
            return

        # Проверяем лимит сообщений
        if not is_not_to_many_messages_in_period(user_id):
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text='Слишком много сообщений, попробуйте позже'
            )
            logger.warning(f"Пользователь {user_id} превысил лимит сообщений")
            return

        # Сохраняем сообщение в БД и пересылаем админам
        create_message_in_db(
            user_id, 
            update.message.from_user.full_name,
            update.message.date.timestamp(), 
            update.message.message_id
        )
        
        await update.message.forward(chat_id=ADMIN_CHAT_ID)
        await context.bot.send_message(
            chat_id=update.message.chat_id, 
            text=MESSAGE_IS_RECEIVED_BY_ADMIN
        )
        
        logger.info(f"Сообщение от пользователя {user_id} переслано админам")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения пользователя: {e}")
        try:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Произошла ошибка при обработке вашего сообщения. Попробуйте позже."
            )
        except Exception as send_error:
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю: {send_error}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}")
    
    if update and update.message:
        try:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Произошла техническая ошибка. Пожалуйста, попробуйте позже."
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")


if __name__ == '__main__':
    try:
        # Инициализация базы данных
        dbhandle.connect()
        Messages.create_table()
        BannedUsers.create_table()
        dbhandle.close()
        logger.info("База данных успешно инициализирована")
    except peewee.InternalError as px:
        logger.error(f"Ошибка инициализации базы данных: {px}")
        print(str(px))
    
    # Создание и настройка приложения
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Добавление обработчиков
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message_to_admin_group))
    application.add_handler(CommandHandler('start', start))
    
    # Добавление глобального обработчика ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Бот запущен и готов к работе")
    application.run_polling()
