import logging

from telethon.sync import TelegramClient

from data.config import API_HASH, API_ID, SESSION


def main():
    logging.basicConfig(level=logging.DEBUG)

    client: TelegramClient = TelegramClient(SESSION, API_ID, API_HASH)

    with client:
        client.run_until_disconnected()


if __name__ == '__main__':
    main()
