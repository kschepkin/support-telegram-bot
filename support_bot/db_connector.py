import datetime
from peewee import *
from settings import (MESSAGE_COUNT_PERIOD, COUNT_OF_MESSAGES_IN_PERIOD, DB_USER,
                      DB_HOST, DB_NAME, DB_PASSWORD)

dbhandle = MySQLDatabase(
    DB_NAME, user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)


class Messages(Model):
    class Meta:
        database = dbhandle
        order_by = ('id',)

    user_id = BigIntegerField()
    user_full_name = CharField()
    message_date = BigIntegerField()
    message_id = BigIntegerField()
    last_reply_time = BigIntegerField(null=True)


class BannedUsers(Model):
    class Meta:
        database = dbhandle
        order_by = ('nickname',)

    user_id = BigIntegerField()
    nickname = CharField(null=True)
    full_name = CharField()


def create_message_in_db(user_id, user_full_name, message_date, message_id):
    dbhandle.connect()
    Messages.create(user_id=user_id, user_full_name=user_full_name,
                    message_date=message_date, message_id=message_id, last_reply_time=None)
    dbhandle.close()


def get_message_id_from_db(user_id, message_date):
    dbhandle.connect()
    message_id = 0
    for i in Messages.select(Messages.message_id).where((Messages.user_id == user_id) &
                                                        (Messages.message_date == message_date)):
        message_id = i.message_id
    dbhandle.close()
    return message_id


def remove_message_from_db(user_id):
    dbhandle.connect()
    query = Messages.delete().where(Messages.user_id == user_id)
    query.execute()
    dbhandle.close()


def set_last_reply_time(user_id, message_date, last_reply_time):
    dbhandle.connect()
    query = Messages.update(last_reply_time=last_reply_time).where((Messages.user_id == user_id) &
                                                                   (Messages.message_date == message_date))
    query.execute()
    dbhandle.close()


def get_last_reply_time(user_id, message_date):
    dbhandle.connect()
    last_reply_time = None
    for i in Messages.select(Messages.last_reply_time).where((Messages.user_id == user_id) &
                                                             (Messages.message_date == message_date)):
        last_reply_time = i.last_reply_time
    dbhandle.close()
    return last_reply_time


def set_new_banned_user(user_id, nickname, full_name):
    dbhandle.connect()
    BannedUsers.create(user_id=user_id, nickname=nickname, full_name=full_name)
    dbhandle.close()


def get_banned_users():
    dbhandle.connect()
    banned_users = [i.user_id for i in BannedUsers.select(BannedUsers.user_id)]
    dbhandle.close()
    return banned_users


def is_not_to_many_messages_in_period(user_id):
    dbhandle.connect()
    count = 0
    for i in Messages.select().where((Messages.user_id == user_id) &
                                     (Messages.message_date > (datetime.datetime.now().timestamp() -
                                                               MESSAGE_COUNT_PERIOD))):
        count += 1
    dbhandle.close()
    if count <= COUNT_OF_MESSAGES_IN_PERIOD:
        return True
    else:
        return False


def get_chat_id_by_full_name_and_date(user_full_name, message_date):
    dbhandle.connect()
    chat_id = None
    for i in Messages.select(Messages.user_id).where((Messages.user_full_name == user_full_name) &
                                                     (Messages.message_date == message_date)):
        chat_id = i.user_id
    dbhandle.close()
    return chat_id
