from typing import AsyncGenerator

from telethon.hints import EntitiesLike
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.patched import Message, MessageService
from telethon.tl.types import MessageActionTopicCreate
from telethon.tl.types.messages import ChannelMessages


async def parsed_messages_generator(
    client: TelegramClient,
    channel: EntitiesLike,
    limit: int = 100
) -> AsyncGenerator[list[Message | MessageService], None]:
    """
    This function is an asynchronous generator that yields lists of messages from a Telegram channel.

    Parameters:
    - client (TelegramClient): An instance of the TelegramClient class from the Telethon library, used for making API calls.
    - channel (EntitiesLike): The Telegram channel entity (username, ID, etc.) from which to fetch messages.
    - limit (int, optional): The maximum number of messages to fetch at a time. Default is 100.

    Returns:
    - AsyncGenerator[list[Message | MessageService], None]: An asynchronous generator that yields lists of messages.

    Yields:
    - list[Message | MessageService]: A list of messages fetched from the Telegram channel.

    Note:
    - It fetches messages in batches of the specified limit until there are no more messages left in the channel.
    - The function yields the fetched messages one batch at a time.
    """
    channel_entity = await client.get_entity(channel)
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

        offset_msg = messages[-1].id


def order_dict_reactions(
        top_messages_by_topic_id: dict[int, dict[Message | list[Message]]],
        topic_id: int,
        message: Message,
        top_size: int = 5
    ) -> None:
    """
    This function orders and updates a dictionary of messages based on their reactions.
    If a message with the same number of reactions already exists in the dictionary,
    it appends the new message to the existing one. If not, it adds the new message to the dictionary.
    The dictionary is sorted based on the number of reactions in descending order.
    If the number of messages for a specific topic exceeds the specified top_size,
    the oldest message is removed.

    Parameters:
    - top_messages_by_topic_id (dict[int, dict[Message | list[Message]]]): A dictionary containing messages organized by topic ID.
    - topic_id (int): The ID of the topic for which the message is being processed.
    - message (Message): The message to be added or updated in the dictionary.
    - top_size (int, optional): The maximum number of messages to keep for each topic. Default is 5.

    Returns:
    - None: The function modifies the input dictionary in-place.
    """
    if topic_id in top_messages_by_topic_id:
        message_added: bool = False

        old_messages: list[Message | list[Message]]
        for old_index, old_messages in enumerate(top_messages_by_topic_id[topic_id]):
            if isinstance(old_messages, list):
                old_message: Message = old_messages[0]
            else:
                old_message: Message = old_messages

            if sum(r.count for r in old_message.reactions.results) == sum(r.count for r in message.reactions.results):
                if isinstance(old_messages, Message):
                    top_messages_by_topic_id[topic_id][old_index] = [old_messages]

                top_messages_by_topic_id[topic_id][old_index].append(message)
                message_added = True
                break

        if not message_added:
            top_messages_by_topic_id[topic_id].append(message)
            top_messages_by_topic_id[topic_id] = sorted(
                top_messages_by_topic_id[topic_id],
                key=lambda m: sum(r.count for r in m.reactions.results) if isinstance(m, Message) else sum(r.count for r in m[0].reactions.results),
                reverse=True
            )

            if len(top_messages_by_topic_id[topic_id]) > top_size:
                del top_messages_by_topic_id[topic_id][-1]

    else:
        top_messages_by_topic_id[topic_id] = [message]


async def get_top_messages(
        client: TelegramClient,
        channel: EntitiesLike,
        top_size: int = 5
    ) -> dict[tuple[int, str], list[Message | list[Message]]]:
    """
    This function fetches and analyzes messages from a specified Telegram channel,
    identifying the top messages based on the number of reactions.

    Parameters:
    - client (TelegramClient): An instance of the TelegramClient class from the Telethon library, used for making API calls.
    - channel (EntitiesLike): The Telegram channel entity (username, ID, etc.) from which to fetch messages.
    - top_size (int, optional): The number of top messages to fetch for each topic. Default is 5.

    Returns:
    - dict[tuple[int, str], list[Message | list[Message]]]: A dictionary containing the top messages for each topic.
    The keys are tuples of (topic_id, topic_name), and the values are lists of messages or lists of messages lists (if there's more than one message at one place).

    Note:
    - The function fetches messages in batches using the parsed_messages_generator function.
    - It identifies the top messages based on the number of reactions using the order_dict_reactions function.
    """
    topic_name_ids: dict[int, str] = dict()
    top_messages_by_topic_id: dict[int, dict[Message | list[Message]]] = dict()

    messages: ChannelMessages
    async for messages in parsed_messages_generator(client, channel):

        message: Message | MessageService
        for message in messages:
            if isinstance(message, Message) and message.reply_to and message.reply_to.forum_topic and message.reactions:
                # topic id contains in reply_to_top_id if there's reply to someone's message, else in reply_to_msg_id
                topic_id = message.reply_to.reply_to_top_id if message.reply_to.reply_to_top_id else message.reply_to.reply_to_msg_id

                order_dict_reactions(top_messages_by_topic_id, topic_id, message, top_size)

            if isinstance(message, MessageService) and isinstance(message.action, MessageActionTopicCreate):
                topic_name_ids[message.id] = message.action.title

    top_messages_by_topic: dict[tuple[int, str], list[Message | list[Message]]] = dict()
    for topic_id, messages in top_messages_by_topic_id.items():
        top_messages_by_topic[(topic_id, topic_name_ids[topic_id])] = messages

    return top_messages_by_topic
