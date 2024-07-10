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

    chat_instance: str = event.raw_text.split()[-1]
    if chat_instance[0] == '@' or not chat_instance[1:].isdigit():
        chat = chat_instance
        chat_id = (await client.get_entity(chat_instance)).id
    else:
        chat = int(chat_instance)
        chat_id = chat_instance[4:]

    top_messages: dict[tuple, list[Message]] = await get_top_messages(client, chat)
    answer: str = ''

    for topic, messages in top_messages.items():
        answer+= f'🏆 Топ сообщений по реакциям в <b>{topic[1]}</b>:\n'
        place: int = 1
        for equally_reacted_messages in messages:
            if isinstance(equally_reacted_messages, Message):
                message = equally_reacted_messages
                sender = message.from_id
                sender: User = await client.get_entity(sender.user_id)
                user: str = ('@' + sender.username) if sender.username else sender.first_name
                reactions_count = sum(reaction.count for reaction in message.reactions.results)
                answer += f'{place}. <a href="https://t.me/c/{chat_id}/{topic[0]}/{message.id}">Рецепт</a> от {user} | Реакций: {reactions_count}\n'

            elif isinstance(equally_reacted_messages, list):
                answer += f'{place}. '
                messages_stringified: list = []
                reactions_count = sum(reaction.count for reaction in equally_reacted_messages[0].reactions.results)

                for message in equally_reacted_messages:
                    sender = message.from_id
                    sender: User = await client.get_entity(sender.user_id)
                    user: str = ('@' + sender.username) if sender.username else sender.first_name

                    messages_stringified.append(f'<a href="https://t.me/c/{chat_id}/{topic[0]}/{message.id}">Рецепт</a> от {user}')

                answer += ' | '.join(messages_stringified)
                answer += f' | Реакций: {reactions_count}\n'

            place += 1
        answer += '\n'

    await event.reply(answer)


@client.on(events.NewMessage(pattern=r'!total (\w+)?', chats=ADMINS))
async def total_cmd_handler(event: events.NewMessage):
    await event.reply('Обработка результатов, подождите...')

    chat_instance: str = event.raw_text.split()[-1]
    if chat_instance[0] == '@' or not chat_instance[1:].isdigit():
        chat = chat_instance
        chat_id = (await client.get_entity(chat_instance)).id
    else:
        chat = int(chat_instance)
        chat_id = chat_instance[4:]

    top_messages: dict[tuple, list[Message]] = await get_top_messages(client, chat)

    for topic, messages in top_messages.items():
        answer = f'🏆 Топ сообщений по реакциям в <b>{topic[1]}</b>:\n'
        place: int = 1
        for equally_reacted_messages in messages:
            if isinstance(equally_reacted_messages, Message):
                message = equally_reacted_messages
                sender = message.from_id
                sender: User = await client.get_entity(sender.user_id)
                user: str = ('@' + sender.username) if sender.username else sender.first_name
                reactions_count = sum(reaction.count for reaction in message.reactions.results)
                answer += f'{place}. <a href="https://t.me/c/{chat_id}/{topic[0]}/{message.id}">Рецепт</a> от {user} | Реакций: {reactions_count}\n'

            elif isinstance(equally_reacted_messages, list):
                answer += f'{place}. '
                messages_stringified: list = []
                reactions_count = sum(reaction.count for reaction in equally_reacted_messages[0].reactions.results)

                for message in equally_reacted_messages:
                    sender = message.from_id
                    sender: User = await client.get_entity(sender.user_id)
                    user: str = ('@' + sender.username) if sender.username else sender.first_name

                    messages_stringified.append(f'<a href="https://t.me/c/{chat_id}/{topic[0]}/{message.id}">Рецепт</a> от {user}')

                answer += ' | '.join(messages_stringified)
                answer += f' | Реакций: {reactions_count}\n'

            place += 1

        await client.send_message(chat_id, message=answer, reply_to=topic[0])

def main():
    client.start()
    client.run_until_disconnected()


if __name__ == '__main__':
    main()
