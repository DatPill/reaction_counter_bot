from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import TelegramClient
from telethon.tl.patched import Message
from telethon.tl.types import PeerUser, User

from utils.parsers import get_top_messages


async def send_top(client: TelegramClient, chat_id: int):
    top_messages: dict[tuple, list[Message]] = await get_top_messages(client, chat_id)

    for topic, messages in top_messages.items():
        answer: str = f'🏆 Топ сообщений по реакциям в <b>{topic[1]}</b>:\n'
        place: int = 1

        equally_reacted_messages: Message | list[Message]
        for equally_reacted_messages in messages:
            if isinstance(equally_reacted_messages, Message):
                message: Message = equally_reacted_messages
                sender: PeerUser = message.from_id
                sender: User = await client.get_entity(sender.user_id)
                user: str = ('@' + sender.username) if sender.username else sender.first_name
                reactions_count: int = sum(reaction.count for reaction in message.reactions.results)
                answer += f'{place}. <a href="https://t.me/c/{chat_id}/{topic[0]}/{message.id}">Рецепт</a> от {user} | Реакций: {reactions_count}\n'

            elif isinstance(equally_reacted_messages, list):
                answer += f'{place}. '
                messages_stringified: list[str] = []
                reactions_count: int = sum(reaction.count for reaction in equally_reacted_messages[0].reactions.results)

                message: Message
                for message in equally_reacted_messages:
                    sender: PeerUser = message.from_id
                    sender: User = await client.get_entity(sender.user_id)
                    user: str = ('@' + sender.username) if sender.username else sender.first_name

                    messages_stringified.append(f'<a href="https://t.me/c/{chat_id}/{topic[0]}/{message.id}">Рецепт</a> от {user}')

                answer += ' | '.join(messages_stringified)
                answer += f' | Реакций: {reactions_count}\n'

            place += 1

        await client.send_message(chat_id, message=answer, reply_to=topic[0])


async def add_chat_timer(
    scheduler: AsyncIOScheduler,
    client: TelegramClient,
    chat_id: int,
    trigger: str,
    hours: str,
    minutes: str,
    end_date: str | None,
) -> Job:
    if trigger == 'cron':
        job = scheduler.add_job(
            func=send_top, args=(client, chat_id,),
            trigger='cron',
            hour=int(hours), minute=int(minutes),
            end_date=end_date
        )
    elif trigger == 'interval':
        job = scheduler.add_job(
            func=send_top, args=(client, chat_id,),
            trigger=trigger,
            hours=int(hours), minutes=int(minutes), seconds=0,
            end_date=end_date
        )

    return job
