# support-telegram-bot
Simple support telegram bot

This bot is ready-to-use for support teams. How it works:
1. User sends the message to bot
2. Bot answers to user that his message is received (default - 'Ваше обращение успешно отправлено. Вам ответят в ближайшее время')
3. Bot forwards the message to admin (or admin group)
4. Admin replies to the message received from bot
5. Bot sends admin's message to user who sent message at p
Administrators can ban users by replying specified message to user's message ('Бан+1' by default)
Bot has anti-spam: by default one user can send 3 messages in one minute

Execute command `docker-compose up -d` to start bot (docker-compose must be installed)

## Explanation of env in docker-compose ##
support_bot
- BOT_TOKEN - bot token received from @BotFather
- ADMIN_CHAT_ID - id of admin (or group of admins) who will answer to user's messages
- BAN_MESSAGE - message which triggers ban of a user
- COUNT_OF_MESSAGES_IN_PERIOD - count of messages which could be sent by user in period defined by COUNT_OF_MESSAGES_IN_PERIOD
- MESSAGE_COUNT_PERIOD - period when user can send count of messages defined by COUNT_OF_MESSAGES_IN_PERIOD
- MESSAGE_IS_RECEIVED_BY_ADMIN - message to user when he sends the message
- START_MESSAGE - message when user runs `start` command (defualt 'Добрый день! Напишите сообщение — и мы обязательно ответим!')
- DB_USER - owner of database
- DB_PASSWORD - batabase owner's password
- DB_NAME - database name
- DB_HOST - database host
message_cleaner
- MESSAGES_TO_DELETE_HOURS - if last reply by admin time to message is less than number defined by that environment variable, it will be deleted from database
- DB_USER - owner of database
- DB_PASSWORD - batabase owner's password
- DB_NAME - database name
- DB_HOST - database host
database:
- see https://hub.docker.com/_/mysql

Note: if you want to to store all message ids from users, you can exclude `message_cleaner` from docker-compose.yaml
