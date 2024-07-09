import logging

from telethon import events
from telethon.sync import TelegramClient
from telethon.tl.patched import Message
from telethon.tl.types import User

from data.config import API_HASH, API_ID, SESSION, ADMINS
from utils.parsers import get_top_messages

logging.basicConfig(level=logging.DEBUG)
client: TelegramClient = TelegramClient(SESSION, API_ID, API_HASH)
client.parse_mode = 'html'


@client.on(events.NewMessage(pattern=r'!parse (\w+)?', chats=ADMINS))
async def parse_cmd_handler(event: events.NewMessage):
    await event.reply('Обработка результатов, подождите...')

    chat_id: list = event.raw_text.split()[-1]
    top_messages: dict[tuple, list[Message]] = await get_top_messages(client, int(chat_id))
    answer: str = ''

    for topic, messages in top_messages.items():
        answer+= f'🏆 Топ сообщений по реакциям в <b>{topic[1]}</b>:\n'
        place: int = 1
        for message in messages:
            sender = message.from_id
            sender: User = await client.get_entity(sender.user_id)
            user: str = sender.username if sender.username else sender.first_name
            reactions_count = sum(reaction.count for reaction in message.reactions.results)
            answer += f'{place}. <a href="https://t.me/c/{chat_id[4:]}/{topic[0]}/{message.id}">Рецепт</a> от @{user} (реакций: {reactions_count})\n'   # TODO: не всегда есть юзернейм
            place += 1
        answer += '\n'

    await event.reply(answer)


client.start()
client.run_until_disconnected()
