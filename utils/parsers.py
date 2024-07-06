from typing import AsyncGenerator

from telethon.hints import EntitiesLike
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.patched import Message, MessageService
from telethon.tl.types.messages import ChannelMessages


async def parsed_messages_generator(
    client: TelegramClient,
    channel: EntitiesLike,
    limit: int = 100
) -> AsyncGenerator[list[Message | MessageService]]:
    """This function yields list of messages. Default limit is 100 messages at a time."""
    channel_entity = client.get_entity(channel)
    offset_msg = 0

    while True:
        history: ChannelMessages = await client(
            GetHistoryRequest(
                peer=channel_entity,
                offset_id=offset_msg,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            )
        )

        if not history.messages:
            break

        messages: list[Message | MessageService] = history.messages
        yield messages

        offset_msg = messages[len(messages)].id
