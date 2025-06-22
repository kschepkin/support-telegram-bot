import datetime
from peewee import *
from settings import (MESSAGE_COUNT_PERIOD, COUNT_OF_MESSAGES_IN_PERIOD, DB_USER,
                      DB_HOST, DB_NAME, DB_PASSWORD)

dbhandle = MySQLDatabase(
    DB_NAME, 
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    charset='utf8mb4'  # Добавляем поддержку utf8mb4
)


class Messages(Model):
    class Meta:
        database = dbhandle
        order_by = ('id',)
        table_name = 'messages'  # Явно указываем имя таблицы

    user_id = BigIntegerField()
    user_full_name = CharField()
    message_date = BigIntegerField()
    message_id = BigIntegerField()
    last_reply_time = BigIntegerField(null=True)


class BannedUsers(Model):
    class Meta:
        database = dbhandle
        order_by = ('nickname',)
        table_name = 'bannedusers'  # Явно указываем имя таблицы

    user_id = BigIntegerField()
    nickname = CharField(null=True)
    full_name = CharField()


def create_message_in_db(user_id, user_full_name, message_date, message_id):
    try:
        dbhandle.connect(reuse_if_open=True)
        Messages.create(user_id=user_id, user_full_name=user_full_name,
                        message_date=message_date, message_id=message_id, last_reply_time=None)
    except Exception as e:
        raise e
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()


def get_message_id_from_db(user_id, message_date):
    try:
        dbhandle.connect(reuse_if_open=True)
        message_id = 0
        for i in Messages.select(Messages.message_id).where((Messages.user_id == user_id) &
                                                            (Messages.message_date == message_date)):
            message_id = i.message_id
        return message_id
    except Exception as e:
        raise e
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()


def remove_message_from_db(user_id):
    try:
        dbhandle.connect(reuse_if_open=True)
        query = Messages.delete().where(Messages.user_id == user_id)
        query.execute()
    except Exception as e:
        raise e
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()


def set_last_reply_time(user_id, message_date, last_reply_time):
    try:
        dbhandle.connect(reuse_if_open=True)
        query = Messages.update(last_reply_time=last_reply_time).where((Messages.user_id == user_id) &
                                                                       (Messages.message_date == message_date))
        query.execute()
    except Exception as e:
        raise e
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()


def get_last_reply_time(user_id, message_date):
    try:
        dbhandle.connect(reuse_if_open=True)
        last_reply_time = None
        for i in Messages.select(Messages.last_reply_time).where((Messages.user_id == user_id) &
                                                                 (Messages.message_date == message_date)):
            last_reply_time = i.last_reply_time
        return last_reply_time
    except Exception as e:
        raise e
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()


def set_new_banned_user(user_id, nickname, full_name):
    try:
        dbhandle.connect(reuse_if_open=True)
        BannedUsers.create(user_id=user_id, nickname=nickname, full_name=full_name)
    except Exception as e:
        raise e
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()


def get_banned_users():
    try:
        dbhandle.connect(reuse_if_open=True)
        banned_users = [i.user_id for i in BannedUsers.select(BannedUsers.user_id)]
        return banned_users
    except Exception as e:
        raise e
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()


def is_not_to_many_messages_in_period(user_id):
    try:
        dbhandle.connect(reuse_if_open=True)
        count = 0
        for i in Messages.select().where((Messages.user_id == user_id) &
                                         (Messages.message_date > (datetime.datetime.now().timestamp() -
                                                                   MESSAGE_COUNT_PERIOD))):
            count += 1
        return count <= COUNT_OF_MESSAGES_IN_PERIOD
    except Exception as e:
        raise e
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()


def get_chat_id_by_full_name_and_date(user_full_name, message_date):
    try:
        dbhandle.connect(reuse_if_open=True)
        chat_id = None
        for i in Messages.select(Messages.user_id).where((Messages.user_full_name == user_full_name) &
                                                         (Messages.message_date == message_date)):
            chat_id = i.user_id
        return chat_id
    except Exception as e:
        raise e
    finally:
        if not dbhandle.is_closed():
            dbhandle.close()
