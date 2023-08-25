import logging


def info(emoji: str, message: str, print_emoji: bool = False):
    if print_emoji:
        logging.info(f"{emoji} {message}")
    else:
        logging.info(message)


def debug(emoji: str, message: str, print_emoji: bool = False):
    if print_emoji:
        logging.debug(f"{emoji} {message}")
    else:
        logging.debug(message)


def error(emoji: str, message: str, print_emoji: bool = False):
    if print_emoji:
        logging.error(f"{emoji} {message}")
    else:
        logging.error(message)
