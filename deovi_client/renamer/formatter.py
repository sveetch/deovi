
class AsciiOutputFormatter:
    """
    The output formatter class to include format methods for message rows.
    """
    def __init__(self):
        self.max_label = None

    def max_label_length(self, tasks):
        """
        Crawl every task to get the bigger name length.

        Returns:
            integer: Length of bigger name or zero if task list is empty.
        """
        if not tasks:
            return 0

        return max([len(k) for k,v in tasks])

    def _format_row(self, index, label=None, message=None, state=None):
        """
        Format row message from given arguments.

        Arguments:
            index (integer): Index integer for current item in the walked list.

        Keyword Arguments:
            label (string): A label to display surrounded and padded.
            message (string): A message to display.
            state (string): State name can be start, default, debug or end. It will
                define how the row will be formatted.

        Returns:
            string: Formatted message.
        """
        content = []

        # Select the string start
        start = "├─ "
        if state == "start":
            start = "┍━{{{}}} ".format(index)
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

        return "".join([start, label, message])
