import json
from pathlib import Path

from slugify import slugify

from ..exceptions import JobValidationError

from .printer import PrinterInterface
from .validators import is_allowed_file


class Job(PrinterInterface):
    """
    Model object to store job parameters.

    Arguments:
        source (pathlib.Path): Job source filepath.
        basepath (pathlib.Path): Basepath for files to apply task.

    Keyword Arguments:
        name (string): Job name, if empty it will be set a dummy name with the source
            filepath.
        tasks (list): List of task to perform on files.
        extensions (list): List of file extensions to filter files. If empty, all file
            extensions are allowed.
        reverse (boolean): Enable reversion of file names when performing tasks.
    """
    DEFAULT_NAME = "Job from '{}'"
    EMPTY_JOB_MATRIX = {
        "name": None,
        "basepath": None,
        "extensions": None,
        "reversed": False,
        "tasks": [],
    }

    def __init__(self, source, basepath, name=None, tasks=None, extensions=None,
                 reverse=False):
        super().__init__()

        self.source = source
        self.name = name or self.DEFAULT_NAME.format(source)
        self.basepath = basepath
        self.tasks = tasks or []
        self.extensions = extensions
        self.reverse = reverse
        self.sort = True

    @classmethod
    def create(cls, basepath, destination=None):
        """
        Create a new empty Job file for given basepath.

        Arguments:
            basepath (string or pathlib.Path): Basepath to set in Job file. It does not
                matter if the basepath already exists or not. If given path is relative
                it will be resolved to an absolute path. Path must be an existing
                directory.

        Keyword Arguments:
            destination (string or pathlib.Path): Destination path for the Job file to
                create. Default to None, so the destination will be the slugified last
                basepath part (``foo`` from ``/home/foo``) at the current working
                directory. This is validated to not be an already existing path.

        Returns:
            pathlib.Path: Path for created Job file.
        """
        if not isinstance(basepath, Path):
            basepath = Path(basepath)

        # If not absolute, force basepath to be absolute from current working directory
        if not basepath.is_absolute():
            basepath = Path.cwd() / basepath
        basepath = basepath.resolve()

        if not basepath.is_dir():
            msg = "🚨 Basepath does not exists or is not a directory: {}"
            raise JobValidationError(msg.format(basepath))

        if not destination:
            # Craft filename from slugified basepath last part
            destination = Path(slugify(basepath.stem)).with_suffix(".json")
        elif not isinstance(destination, Path):
            destination = Path(destination)

        # If not absolute, force destination to be absolute from current working
        # directory
        if not destination.is_absolute():
            destination = Path.cwd() / destination
        destination = destination.resolve()

        # Finally check destination is a file and its directory exist
        if destination.is_dir():
            msg = "🚨 Destination path must be a file, not an existing directory: {}"
            raise JobValidationError(msg.format(destination))
        elif not destination.parents[0].exists():
            msg = "🚨 Destination path must point into an existing directory: {}"
            raise JobValidationError(msg.format(destination))

        content = Job.EMPTY_JOB_MATRIX.copy()
        content["basepath"] = str(basepath)

        with destination.open("w") as fp:
            json.dump(content, fp, indent=4)

        return destination

    @classmethod
    def load(cls, source):
        """
        Load Job parameters from a filepath and return a model instance.

        This assumes the job have already be validated before from
        ``validate_job_file`` validator.

        Arguments:
            source (string or pathlib.Path): Path to the Job file to load.

        Returns:
            Job: Instance of model configured with job parameters.
        """
        if not isinstance(source, Path):
            source = Path(source)

        with source.open("r") as fp:
            data = json.load(fp)

        # If relative path, resolve it from the source directory
        basepath = Path(data["basepath"])
        if not basepath.is_absolute():
            basepath = (source.parents[0] / basepath).resolve()

        return cls(
            source,
            basepath,
            name=data.get("name", None),
            tasks=data["tasks"],
            extensions=data.get("extensions", None),
            reverse=data.get("reversed", False),
        )

    def get_target_files(self):
        """
        Return list of eligible files from job basepath depending allowed extensions.

        This is not recursive.

        Returns:
            list: List of Path objects eligible files.
        """
        files = []

        msg = self.extensions or ["All"]
        self.log_info(" • Allowed file extension(s): {}".format(", ".join(msg)))

        for filename in self.basepath.iterdir():
            if is_allowed_file(filename, extensions=self.extensions):
                files.append(filename)

        if self.sort:
            files = sorted(files)

        if self.reverse:
            files = reversed(files)

        self.log_info(" • {} files to process".format(len(files)))

        return files

    def run(self, task_manager, dry_run=True):
        """
        Run all job tasks.

        Arguments:
            task_manager (tasks.TaskMaster): The task manager to use to run tasks.

        Keyword Arguments:
            dry_run (boolean): To enable "dry run" mode which does not write anything.
                If disabled, every renaming will be writed to the filesystem. Disabled
                by default.

        Returns:
            dict: A dictionnary of informations about original sources and renaming.
        """
        # A list of renamed filenames used for statistic and warning about overwritting
        # in dry run mode
        rename_store = set([])
        # A list of tuple "(renamed, original)" to restore everything if needed
        reverse_store = []

        self.log_info("📂 Working on: {}".format(self.basepath))

        # A list of original source filenames
        original_store = self.get_target_files()
        self.log_info("")

        # Build row indice and indentation stuff. Indentation length is computed
        # from indice string for the biggest index value
        indentation, indicer = self.get_indentation_infos(
            len(original_store), "[{i}]━",
        )

        # Safely run task, in case of any exception, renamed file will be restored to
        # their original name
        try:
            for i, source in enumerate(original_store, start=1):
                msg = "From: {}".format(source.name)
                self.log_info(msg, state="start", indent=indicer(i))
                # Start destination from original which will be update along the tasks
                destination = source

                # Perform task to alter destination to final renamed filename
                for name, options in self.tasks:
                    task_method = "task_{}".format(name)

                    # Perform task
                    paths = getattr(task_manager, task_method)(
                        i,  destination, _indent=indentation, **options
                    )

                    # Update destination filename from returned task value
                    destination = paths[1]

                # If final destination is not the same as the original
                if destination != source:

                    # Error if file already exists, no overwritting is allowed
                    if destination.exists():
                        msg = (
                            "❗ Destination already exists and won't be overwritten: {}"
                        ).format(
                            destination.name
                        )
                        self.log_warning(msg, state="end", indent=indentation)
                    elif destination in rename_store:
                        msg = (
                            "❗ This destination is already planned from another file:"
                            " {}"
                        ).format(
                            destination.name
                        )
                        self.log_warning(msg, state="end", indent=indentation)
                    # Dry run mode just output results without writing anything
                    elif dry_run:
                        msg = "✨ To: {}".format(destination.name)
                        self.log_info(msg, state="end", indent=indentation)
                        rename_store.add(destination)
                    # Effective renaming
                    else:
                        msg = "✅ To: {}".format(destination.name)
                        self.log_info(msg, state="end", indent=indentation)
                        reverse_store.append(
                            (source, destination)
                        )
                        # Perform renaming
                        source.rename(destination)
                        rename_store.add(destination)
                    # White space divider between jobs
                    self.log_info("")
                # If source and destination are identical, nothing to do, just warning
                else:
                    msg = (
                        "❗ Source and destination paths are identical, nothing to "
                        "rename."
                    )
                    self.log_warning(msg, state="end", indent=indentation)
                    self.log_warning("")
        except:  # noqa: E722
            # Restore every renamed files before error
            msg = (
                "🚨 An error occured during a job, every files will be "
                "restored with their original filename."
            )
            self.log_error("")
            self.log_error(msg)
            self.log_error("")

            # Restore renamed file to their original filenames
            for source, destination in reverse_store:
                self.log_error("*", destination, "=>", source)
                source.rename(destination, source)
            self.log_error("")

            # Finally raise the original error
            raise

        return {
            "original_store": original_store,
            "rename_store": rename_store,
        }
