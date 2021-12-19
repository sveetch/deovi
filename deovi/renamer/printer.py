import logging


class PrinterInterface:
    """
    Printer interface to output messages.

    This is a common interface for objects to use logging and optional message
    formatting.
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("deovi")
        self.max_label = 0

    def set_label_length(self, tasks):
        """
        Crawl every task to get the bigger name length.

        Arguments:
            tasks (dict): A dictionnary of tasks infos, only its keys are used to
                compute max value.

        Returns:
            integer: Length of bigger name or zero if task list is empty.
        """
        if not tasks:
            return 0

        return max([len(k) for k, v in tasks])

    def get_indentation_infos(self, length, template):
        """
        Return computated indice and indentation informations.

        Arguments:
            length (integer): Length of items to compute maximum indentation value.
            template (string): String template to build formatted indice.

        Returns:
            tuple: In order, the indentation length (integer) and the indice formatter
                function. This one attempt only an integer value and return a string.
        """
        zfill = len(
            str(length)
        )

        indent_length = len(
            template.format(i=length)
        )

        indice_func = None

        # The formatter function carry the template to format indice directly from
        # given integer
        def indice_func(index):
            return template.format(i=str(index).zfill(zfill))

        return indent_length, indice_func

    def _row_format(self, message, label=None, state=None, indent=None):
        """
        Format row message from given arguments.

        Keyword Arguments:
            message (string): A message to display.
            state (string): State name can be start, default, debug or end. It will
                define how the row will be formatted.
            indent (integer or string): If a string, use it to prefix message. If an
                integer, define the number of space to be added as prefix.

        Returns:
            string: Formatted message.
        """
        prefix = ""

        if indent and isinstance(indent, int):
            prefix = " " * indent
        elif indent:
            prefix = indent

        # Select the leading string to insert before label or message
        start = "├─ "
        if state == "start":
            start = "┍━ "
        elif state == "debug":
            start = "├┄ "
        elif state == "end":
            start = "┕━ "

        # Add label surrounding and padding
        label = label or ""
        if label:
            template = "[{}]  "
            label = template.format(label)
            label = label.ljust(len(template.format("")) + self.max_label)

        # Put message if any
        message = message or ""

        return "".join([prefix, start, label, message])

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
        if "label" in kwargs or "state" in kwargs or "indent" in kwargs:
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
