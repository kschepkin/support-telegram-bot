import time
import datetime
from peewee import *
from settings import DB_USER, DB_HOST, DB_NAME, DB_PASSWORD, MESSAGES_TO_DELETE_HOURS


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


def remove_obsolete_messages():
    edge = datetime.datetime.now().timestamp() - MESSAGES_TO_DELETE_HOURS * 3600
    dbhandle.connect()
    query = Messages.delete().where(Messages.last_reply_time < edge)
    query.execute()
    dbhandle.close()


while True:
    remove_obsolete_messages()
    time.sleep(86400)
