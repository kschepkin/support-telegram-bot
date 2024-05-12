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


def get_origin_message_chat_id(forward_origin_message):
    if forward_origin_message['type'] == telegram.constants.MessageOriginType.USER:
        return forward_origin_message['sender_user']['id']
    if forward_origin_message['type'] == telegram.constants.MessageOriginType.HIDDEN_USER:
        user_full_name = forward_origin_message['sender_user_name']
        date_of_sending = forward_origin_message['date']
        return get_chat_id_by_full_name_and_date(user_full_name, date_of_sending)


def get_user_full_name_by_origin_message(forward_origin_message):
    if forward_origin_message['type'] == telegram.constants.MessageOriginType.USER:
        return (f'{forward_origin_message["sender_user"]["first_name"]} '
                f'{forward_origin_message["sender_user"]["last_name"]}')
    if forward_origin_message['type'] == telegram.constants.MessageOriginType.HIDDEN_USER:
        return forward_origin_message['sender_user_name']


def get_user_nickname_by_origin_message(forward_origin_message):
    if forward_origin_message['type'] == telegram.constants.MessageOriginType.USER:
        return forward_origin_message['sender_user']['username']
    else:
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.message.chat_id, text=START_MESSAGE)


async def forward_message_to_admin_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id == ADMIN_CHAT_ID:
        if update.message.text == BAN_MESSAGE:
            forward_origin_message = update.message.reply_to_message.forward_origin.to_dict()
            origin_message_chat_id = get_origin_message_chat_id(forward_origin_message)
            origin_message_user_nickname = get_user_nickname_by_origin_message(forward_origin_message)
            origin_message_user_full_name = get_user_full_name_by_origin_message(forward_origin_message)
            set_new_banned_user(origin_message_chat_id, origin_message_user_nickname, origin_message_user_full_name)
            remove_message_from_db(update.message.from_user.id)
        else:
            forward_origin_message = update.message.reply_to_message.forward_origin.to_dict()
            origin_message_chat_id = get_origin_message_chat_id(forward_origin_message)
            origin_message_timestamp = forward_origin_message['date']
            reply_parameters = telegram.ReplyParameters(message_id=get_message_id_from_db(origin_message_chat_id,
                                                                                          origin_message_timestamp),
                                                        chat_id=origin_message_chat_id)
            if update.message.text is not None:
                await context.bot.send_message(chat_id=origin_message_chat_id,
                                               text=update.message.text,
                                               reply_parameters=reply_parameters)
            elif update.message.document is not None:
                await context.bot.send_document(chat_id=origin_message_chat_id,
                                                document=update.message.document.file_id,
                                                caption=update.message.caption,
                                                reply_parameters=reply_parameters)
            elif update.message.audio is not None:
                await context.bot.send_audio(chat_id=origin_message_chat_id,
                                             audio=update.message.audio.file_id,
                                             caption=update.message.caption,
                                             reply_parameters=reply_parameters)
            elif update.message.video is not None:
                await context.bot.send_video(chat_id=origin_message_chat_id,
                                             video=update.message.video.file_id,
                                             caption=update.message.caption,
                                             reply_parameters=reply_parameters)
            elif update.message.animation is not None:
                await context.bot.send_animation(chat_id=origin_message_chat_id,
                                                 animation=update.message.animation.file_id,
                                                 caption=update.message.caption,
                                                 reply_parameters=reply_parameters)
            elif update.message.photo != ():
                await context.bot.send_photo(chat_id=origin_message_chat_id,
                                             photo=update.message.photo[0].file_id,
                                             caption=update.message.caption,
                                             reply_parameters=reply_parameters)
            elif update.message.sticker is not None:
                await context.bot.send_sticker(chat_id=origin_message_chat_id,
                                               sticker=update.message.sticker.file_id,
                                               reply_parameters=reply_parameters)
            elif update.message.voice is not None:
                await context.bot.send_voice(chat_id=origin_message_chat_id,
                                             voice=update.message.voice.file_id,
                                             caption=update.message.caption,
                                             reply_parameters=reply_parameters)
            else:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text='Сообщние не доставлено. '
                                                                           'Неподдерживаемый формат сообщения')
            set_last_reply_time(user_id=origin_message_chat_id, message_date=origin_message_timestamp,
                                last_reply_time=datetime.datetime.now().timestamp())
    else:
        if update.message.from_user.id in get_banned_users():
            await context.bot.send_message(chat_id=update.message.chat_id, text=MESSAGE_IS_RECEIVED_BY_ADMIN)
        else:
            if is_not_to_many_messages_in_period(update.message.from_user.id):
                create_message_in_db(update.message.from_user.id, update.message.from_user.full_name,
                                     update.message.date.timestamp(), update.message.message_id)
                await update.message.forward(chat_id=ADMIN_CHAT_ID)
                await context.bot.send_message(chat_id=update.message.chat_id, text=MESSAGE_IS_RECEIVED_BY_ADMIN)
            else:
                await context.bot.send_message(chat_id=update.message.chat_id,
                                               text=f'Слишком много сообщений, попробуйте позже')


if __name__ == '__main__':
    try:
        dbhandle.connect()
        Messages.create_table()
        BannedUsers.create_table()
        dbhandle.close()
    except peewee.InternalError as px:
        print(str(px))
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message_to_admin_group))
    application.add_handler(CommandHandler('start', start))
    application.run_polling()
