import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.job import Job

from telethon import events
from telethon.sync import TelegramClient
from telethon.tl.patched import Message
from telethon.tl.types import User

from data.config import API_HASH, API_ID, SESSION, ADMINS
from utils.parsers import get_top_messages
from utils.scheduler import add_chat_timer


# Set up Telegram client
logging.basicConfig(level=logging.DEBUG)
client: TelegramClient = TelegramClient(SESSION, API_ID, API_HASH)
client.parse_mode = 'html'

# Set up scheduler
scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
channel_timers: dict[int, Job] = {}

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


@client.on(events.NewMessage(pattern=r'!timer_on (\w+)?', chats=ADMINS))
async def timer_on_cmd_handler(event: events.NewMessage):
    """Examples:

    - `!timer_on @chat at 12:00 until 01.01.2027`
    - `!timer_on @chat every 24h until 31.05.2024`
    - `!timer_on @chat every 1h 30m`
    """
    all_data: list[str] = event.raw_text.split()

    chat_instance: str = all_data[1]
    if chat_instance[0] == '@' or not chat_instance[1:].isdigit():
        chat_id: int = (await client.get_entity(chat_instance)).id
    else:
        chat_id: int = int(chat_instance[4:])

    timing: str = all_data[2]
    end_date: str | None = None
    hours: str | None = None
    minutes: str | None = None

    if all_data[-2] == 'until' or all_data[-2] == 'untill' or all_data[-2] == 'до':
        end_date_raw: str = all_data[-1]
        date_list: list = []
        for piece in end_date_raw.split('.')[::-1]:
            date_list.append(piece)
        if len(date_list[0]) < 4:
            date_list[0] = '20' + date_list[0]
        end_date: str = '-'.join(date_list)
        del all_data[-2:]

    if timing == 'at':
        trigger: str = 'cron'

        hours: str = all_data[3].split(':')[0]
        try:
            minutes: str = all_data[3].split(':')[1]
        except IndexError:
            minutes = '00'

    elif timing == 'every':
        trigger: str = 'interval'

        for interval in all_data[3:]:
            if interval.endswith('m') or interval.endswith('м') or interval.endswith('мин') or interval.endswith('min'):
                minutes: str = interval[:-1]
            elif interval.endswith('h') or interval.endswith('hour') or interval.endswith('ч') or interval.endswith('час'):
                hours: str = interval[:-1]

            if not hours:
                hours = '00'
            if not minutes:
                minutes = '00'

    job: Job = await add_chat_timer(
        scheduler=scheduler, client=client,
        chat_id=chat_id, trigger=trigger,
        hours=hours, minutes=minutes,
        end_date=end_date
    )

    if chat_id in channel_timers:
        channel_timers[chat_id].remove()

    channel_timers[chat_id] = job
    await event.reply('Таймер успешно установлен')


@client.on(events.NewMessage(pattern=r'!timer_off (\w+)?', chats=ADMINS))
async def timer_off_cmd_handler(event: events.NewMessage):
    all_data: list[str] = event.raw_text.split()

    chat_instance: str = all_data[-1]
    if chat_instance[0] == '@' or not chat_instance[1:].isdigit():
        chat_id: int = (await client.get_entity(chat_instance)).id
    else:
        chat_id: int = int(chat_instance[4:])

    if chat_id in channel_timers:
        channel_timers[chat_id].remove()
        del channel_timers[chat_id]
        await event.reply('Таймер успешно удалён')

    else:
        await event.reply('Для указанной группы нет таймера')


def main():
    client.start()
    scheduler.start()
    client.run_until_disconnected()


if __name__ == '__main__':
    main()
