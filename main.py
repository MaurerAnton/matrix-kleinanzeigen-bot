import asyncio
import logging
import sys

from mkb.bot import KleinanzeigenBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)


def main():
    bot = KleinanzeigenBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        asyncio.run(bot.client.close())


if __name__ == "__main__":
    main()
