import sys
from loguru import logger

from bruh import claim_tokens


def main():
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | {level}: <level>{message}</level>",
    )

    private_keys = open("private_keys.txt").read().splitlines()

    if not private_keys:
        logger.error("No private keys found, please add them to private_keys.txt")
        return

    for private_key in private_keys:
        try:
            claim_tokens(private_key)
        except Exception as e:
            logger.error(e)


if __name__ == "__main__":
    main()
