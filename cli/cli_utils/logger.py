import logging


def info(emoji: str, message: str, print_emoji: bool = False) -> None:
    """
    Logs an info message.
    :param emoji: Emoji to print
    :param message: Message to print
    :param print_emoji: Print emoji or not
    """
    if print_emoji:
        logging.info("%s: %s", emoji, message)
    else:
        logging.info(message)


def debug(emoji: str, message: str, print_emoji: bool = False) -> None:
    """
    Logs a debug message.
    :param emoji: Emoji to print
    :param message: Message to print
    :param print_emoji: Print emoji or not
    """
    if print_emoji:
        logging.info("%s: %s", emoji, message)
    else:
        logging.debug(message)


def error(emoji: str, message: str, print_emoji: bool = False) -> None:
    """
    Logs an error message.
    :param emoji: Emoji to print
    :param message: Message to print
    :param print_emoji: Print emoji or not
    """
    if print_emoji:
        logging.info("%s: %s", emoji, message)
    else:
        logging.error(message)
