import logging
from pathlib import Path


class PrinterInterface:
    """
    Printer interface to output messages.

    This is a common interface for objects to use logging and optional message
    formatting.
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("deovi-client")
        self.max_label = 0

    def set_label_length(self, tasks):
        """
        Crawl every task to get the bigger name length.

        NOTE:
            Let's forget this feature ?

        Returns:
            integer: Length of bigger name or zero if task list is empty.
        """
        if not tasks:
            return 0

        return max([len(k) for k, v in tasks])

    def _row_format(self, message, label=None, state=None):
        """
        Format row message from given arguments.

        Keyword Arguments:
            message (string): A message to display.
            state (string): State name can be start, default, debug or end. It will
                define how the row will be formatted.

        Returns:
            string: Formatted message.
        """
        content = []

        # Select the leading string to insert before label or message
        start = " ├─ "
        if state == "start":
            start = " ┍━ "
        elif state == "debug":
            start = " ├┄ "
        elif state == "end":
            start = " ┕━ "

        # Add label surrounding and padding
        label = label or ""
        if label:
            template = "[{}]  "
            label = template.format(label)
            label = label.ljust(len(template.format("")) + self.max_label)

        # Put message if any
        message = message or ""

        return "".join([start, label, message])

    def log(self, level, message, **kwargs):
        """
        Log message at required level with or without formatting.

        If method receives either ``label`` or ``state`` keyword arguments, message
        will be formatted using ``_row_format`` (which keyword arguments are passed to)
        before to be logged.

        Else the message is just logged without formatting.

        Arguments:
            level (string): Logging level name (``debug``, ``info``, etc..).
        """
        if "label" in kwargs or "state" in kwargs:
            getattr(self.logger, level)(
                self._row_format(message, **kwargs)
            )
        else:
            getattr(self.logger, level)(message)

    def log_debug(self, *args, **kwargs):
        """
        Shortcut to log message at debug level.
        """
        self.log("debug", *args, **kwargs)

    def log_info(self, *args, **kwargs):
        """
        Shortcut to log message at info level.
        """
        self.log("info", *args, **kwargs)

    def log_warning(self, *args, **kwargs):
        """
        Shortcut to log message at warning level.
        """
        self.log("warning", *args, **kwargs)

    def log_error(self, *args, **kwargs):
        """
        Shortcut to log message at error level.
        """
        self.log("error", *args, **kwargs)

    def log_critical(self, *args, **kwargs):
        """
        Shortcut to log message at critical level.
        """
        self.log("critical", *args, **kwargs)
