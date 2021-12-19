from .printer import PrinterInterface


class TaskMethods:
    """
    Task method container mixin to inherit for basic tasks.

    All method which start with "task_" is assumed to be a task method. Task
    methods should set an attribute "required" for validation, if this attribute is not
    set or empty, we assume there is no validation to do for the task.

    Note than task NEVER write anything, they just returns a tuple with original source
    filename as first item and second item is the resulting filename from task.

    All tasks assume given path are files, no further validation will be done on given
    file paths.

    Also tasks only works with Path objects, no string for file paths are allowed.

    Keyword Arguments:
        formatter (object):
    """

    def task_capitalize(self, index, source, **options):
        """
        Capitalize file name.

        Work on the whole filename including extension.

        Arguments:
            index (integer): Index integer for current item in the walked list. Mostly
                used for print out message.

            source (pathlib.Path): Source filename.
            **options (dict): Tasks options, this task does not expect any options.

        Returns:
            tuple: A tuple of Path objects for respectively original and renamed
            filename Path.
        """
        destination = source.with_name(source.name.capitalize())

        self.log_debug(
            destination.name,
            label="capitalize",
            state="debug",
            indent=options.get("_indent"),
        )

        return (source, destination)

    def task_lowercase(self, index, source, **options):
        """
        Lowercase file name.

        Work on the whole filename including extension.

        Arguments:
            index (integer): Index integer for current item in the walked list. Mostly
                used for print out message.

            source (pathlib.Path): Source Path object.
            **options (dict): Tasks options, this task does not expect any options.

        Keyword Arguments:
            verbose (string): To enable or disable verbosity, when disable not any
                output will be printed out. Default to False.
            printer (function): A function to use to print out message. If not set,
                ``verbose`` argument is useless. Default to None.

        Returns:
            tuple: A tuple of current filename and new filename.
        """
        destination = source.with_name(source.name.lower())

        self.log_debug(
            destination.name,
            label="lowercase",
            state="debug",
            indent=options.get("_indent"),
        )

        return (source, destination)

    def task_uppercase(self, index, source, **options):
        """
        Uppercase file name.

        Work on the whole filename including extension.

        Arguments:
            index (integer): Index integer for current item in the walked list. Mostly
                used for print out message.

            source (pathlib.Path): Source Path object.
            **options (dict): Tasks options, this task does not expect any options.

        Keyword Arguments:
            verbose (string): To enable or disable verbosity, when disable not any
                output will be printed out. Default to False.
            printer (function): A function to use to print out message. If not set,
                ``verbose`` argument is useless. Default to None.

        Returns:
            tuple: A tuple of current filename and new filename.
        """
        destination = source.with_name(source.name.upper())

        self.log_debug(
            destination.name,
            label="uppercase",
            state="debug",
            indent=options.get("_indent"),
        )

        return (source, destination)

    def task_underscore_to_dash(self, index, source, **options):
        """
        Convert some strings into another ones:

        * "_" to "-";
        * "---" to "_";

        So "ping_-_foo_bar.mp4" will be converted to "ping_foo-bar.mp4".

        Work on the whole filename including extension.

        Arguments:
            index (integer): Index integer for current item in the walked list. Mostly
                used for print out message.

            source (pathlib.Path): Source Path object.
            **options (dict): Tasks options, this task does not expect any options.

        Keyword Arguments:
            verbose (string): To enable or disable verbosity, when disable not any
                output will be printed out. Default to False.
            printer (function): A function to use to print out message. If not set,
                ``verbose`` argument is useless. Default to None.

        Returns:
            tuple: A tuple of current filename and new filename.
        """
        destination = source.with_name(
            source.name.replace("_", "-").replace("---", "_")
        )

        self.log_debug(
            destination.name,
            label="underscore_to_dash",
            state="debug",
            indent=options.get("_indent"),
        )

        return (source, destination)

    def task_add_prefix(self, index, source, **options):
        """
        Add a prefix before filename.

        Work on the whole filename including extension.

        Arguments:
            index (integer): Index integer for current item in the walked list. Mostly
                used for print out message.

            source (pathlib.Path): Source Path object.
            **options (dict): Tasks options, expect an option "prefix".

        Keyword Arguments:
            verbose (string): To enable or disable verbosity, when disable not any
                output will be printed out. Default to False.
            printer (function): A function to use to print out message. If not set,
                ``verbose`` argument is useless. Default to None.

        Returns:
            tuple: A tuple of current filename and new filename.
        """
        prefix = options["prefix"]

        destination = source.with_name(prefix + source.name)

        self.log_debug(
            destination.name,
            label="add_prefix",
            state="debug",
            indent=options.get("_indent"),
        )

        return (source, destination)
    task_add_prefix.required = ["prefix"]

    def task_numerate(self, index, source, **options):
        """
        Add current index position of item in file list.

        Index number is filled (from given zfill length) to the right with '0' and
        divided from filename with given divider string.

        Arguments:
            index (integer): Index integer for current item in the walked list. Mostly
                used for print out message.

            source (pathlib.Path): Source Path object.
            **options (dict): Tasks options, expect option "zfill" and optional
                "start" and "divider".

        Keyword Arguments:
            verbose (string): To enable or disable verbosity, when disable not any
                output will be printed out. Default to False.
            printer (function): A function to use to print out message. If not set,
                ``verbose`` argument is useless. Default to None.

        Returns:
            tuple: A tuple of current filename and new filename.
        """
        zfill = options["zfill"]
        start = options.get("start", 0)
        divider = options.get("divider", "_")

        new_filename = "{index}{divider}{filename}".format(
            index=str(start + index).zfill(zfill),
            divider=divider,
            filename=source.name,
        )

        destination = source.with_name(new_filename)

        self.log_debug(
            destination.name,
            label="numerate",
            state="debug",
            indent=options.get("_indent"),
        )

        return (source, destination)
    task_numerate.required = ["zfill"]

    def task_catch_segments(self, index, source, **options):
        """
        Catch segments from filename.

        Filename is splitted on a divider and only required segments from given rules
        are retained then joined.

        This only apply on the file name part, not the extension parts.

        Joiner option  can use a custom string to join segments, default string if not
        given is "-".

        Arguments:
            index (integer): Index integer for current item in the walked list. Mostly
                used for print out message.
            source (pathlib.Path): Source Path object.
            **options (dict): Tasks options, require options "divider" and
                "slice_start" and accept optional "slice_end" and "joiner".

        Keyword Arguments:
            verbose (string): To enable or disable verbosity, when disable not any
                output will be printed out. Default to False.
            printer (function): A function to use to print out message. If not set,
                ``verbose`` argument is useless. Default to None.

        Returns:
            tuple: A tuple of current filename and new filename.
        """
        divider = options["divider"]
        joiner = options.get("joiner", "-")
        slice_start = options["slice_start"]
        slice_end = options.get("slice_end", None)

        # Get the filename root, eg: without file extension
        root = source.stem
        # Get the file extension if any
        ext = ""
        if len(source.suffixes) > 0:
            ext = source.suffixes[-1]

        # Split name on divider
        segments = root.split(divider)
        # Only remove segment if there is more than one
        if len(segments) > 1:
            if slice_end:
                segments = segments[slice_start:slice_end]
            else:
                segments = segments[slice_start:]

        # Add again the file extension to modified filename root
        new_filename = joiner.join(segments) + ext

        destination = source.with_name(new_filename)

        self.log_debug(
            destination.name,
            label="catch_segments",
            state="debug",
            indent=options.get("_indent"),
        )

        return (source, destination)
    task_catch_segments.required = ["divider", "slice_start"]

    def task_replace(self, index, source, **options):
        """
        Replace all occurences in a string (from) by another one (to).

        This is applied on the whole filename, including the file extensions.

        Arguments:
            index (integer): Index integer for current item in the walked list. Mostly
            used for print out message.
            source (pathlib.Path): Source Path object.
            **options (dict): Tasks options, expect options "from" and "to".

        Keyword Arguments:
            verbose (string): To enable or disable verbosity, when disable not any
                output will be printed out. Default to False.
            printer (function): A function to use to print out message. If not set,
                ``verbose`` argument is useless. Default to None.

        Returns:
            tuple: A tuple of current filename and new filename.
        """
        from_string = options["from"]
        to_string = options["to"]

        destination = source.with_name(
            source.name.replace(from_string, to_string)
        )

        self.log_debug(
            destination.name,
            label="replace",
            state="debug",
            indent=options.get("_indent"),
        )

        return (source, destination)
    task_replace.required = ["from", "to"]


class TaskMaster(PrinterInterface, TaskMethods):
    """
    Task manager glues classes for printer and method implementations.
    """
    pass
