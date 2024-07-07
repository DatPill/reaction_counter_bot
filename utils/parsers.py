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

        offset_msg = messages[len(messages)].id


def order_dict_reactions(
        top_messages_by_thread_id: dict[int, Message],
        thread_id: int,
        message: Message,
        top_size: int = 3
    ) -> None:
    """
    Modifies the `top_messages_by_thread_id` dictionary by adding a new message and sorting it based on reactions.

    Parameters:
    - top_messages_by_thread_id (dict[int, Message]): A dictionary where the keys are thread IDs and the values are lists of messages.
    - thread_id (int): The ID of the thread to which the message belongs.
    - message (Message): The message to be added to the thread.
    - top_size (int, optional): The maximum number of messages to keep in each thread. Default is 3.

    Returns:
    None

    Side Effects:
    - Modifies the `top_messages_by_thread_id` dictionary by adding the new message and sorting it based on reactions.
    - If the number of messages in the thread exceeds the specified top size, the less reacted message is removed.
    """
    if thread_id in top_messages_by_thread_id:
        top_messages_by_thread_id[thread_id].append(message)
        top_messages_by_thread_id[thread_id] = sorted(top_messages_by_thread_id[thread_id], key=lambda m: sum(r.count for r in m.reactions.results), reverse=True)  # FIXME

        if len(top_messages_by_thread_id[thread_id]) > top_size:
            del top_messages_by_thread_id[thread_id][-1]

    else:
        top_messages_by_thread_id[thread_id] = [message]


async def get_top_messages(
        client: TelegramClient,
        channel: EntitiesLike,
        top_size: int = 5
    ) -> dict[str, list[Message]]:
    """
    Returns a dictionary of top reacted messages in each thread.

    Parameters:
    - client (TelegramClient): The Telegram client instance for making API calls.
    - channel (EntitiesLike): The channel entity (username, ID, etc.) from which to fetch messages.
    - top_size (int): How many messages will be in top.

    Returns:
    - dict[str, list[Message]]: A dictionary where the keys are thread names and the values are lists of top messages in each thread.

    Return format:
    ```
    {
        "thread_name": [Message, Message, ..., Message],
        "thread_name": [Message, Message, ..., Message]
    }
    ```

    Note:
    - This function fetches messages using the parsed_messages_generator function.
    - It identifies threads by checking the reply_to attribute of messages.
    - It uses the order_dict_reactions function to order messages by reactions.
    - It populates thread_name_ids dictionary with thread IDs and names.
    - It populates top_messages_by_thread_id dictionary with thread IDs and top messages.
    - It returns a dictionary with thread names and their corresponding top messages.
    """
    thread_name_ids: dict[int, str] = dict()
    top_messages_by_thread_id: dict[int, Message] = dict()

    messages: ChannelMessages
    async for messages in parsed_messages_generator(client, channel):

        message: Message | MessageService
        for message in messages:
            if isinstance(message, Message) and message.reply_to and message.reply_to.forum_topic and message.reactions:
                # thread id contains in reply_to_top_id if there's reply to someone's message, else in reply_to_msg_id
                thread_id = message.reply_to.reply_to_top_id if message.reply_to.reply_to_top_id else message.reply_to.reply_to_msg_id

                order_dict_reactions(top_messages_by_thread_id, thread_id, message, top_size)


            if isinstance(message, MessageService) and isinstance(message.action, MessageActionTopicCreate):
                thread_name_ids[message.id] = message.action.title

        top_messages_by_thread_name: dict[str, list[Message]] = dict()
        for thread_id, messages in top_messages_by_thread_id.items():
            top_messages_by_thread_name[thread_name_ids[thread_id]] = messages

        return top_messages_by_thread_name
