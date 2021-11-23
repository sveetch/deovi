import json
import logging
from pathlib import Path

from ..exceptions import JobValidationError, TaskValidationError

from .printer import PrinterInterface
from .validators import is_allowed_file


class Job(PrinterInterface):
    """
    Model object to store job parameters.

    Also transform every path string to Path object.

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
    def load(cls, source):
        """
        Load Job parameters from a filepath and return a model instance.

        This assumes the job have already be validated before from
        ``validate_job_file`` validator.

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
            path = self.basepath / filename
            if is_allowed_file(filename, extensions=self.extensions):
                files.append(filename)

        if self.sort:
            files = sorted(files)

        if self.reverse:
            files = reversed(files)

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
        """
        # A list of renamed filenames used for statistic and warning about overwritting
        # in dry run mode
        rename_store = set([])
        # A list of tuple "(renamed, original)" to restore everything if needed
        reverse_store = []

        self.log_info("")
        self.log_info("📂 Working on: {}".format(self.basepath))

        # A list of original source filenames
        original_store = self.get_target_files()

        # Safely run task, in case of any exception, renamed file will be restored to
        # their original name
        try:
            for i, source in enumerate(original_store, start=1):
                self.log_info("")
                msg = "From: {}".format(source.name)
                self.log_info(msg, state="start")
                # Start destination from original which will be update along the tasks
                destination = source

                # Perform task to alter destination to final renamed filename
                for name, options in self.tasks:
                    task_method = "task_{}".format(name)

                    # Perform task
                    paths = getattr(task_manager, task_method)(
                        i,  destination,  **options
                    )

                    # Update destination filename from returned task value
                    destination = paths[1]

                # If final destination is not the same as the original
                if destination != source:
                    print()
                    print(source, "=>", destination)

                    # Error if file already exists, no overwritting is allowed
                    if destination.exists():
                        msg = (
                            "❗ Destination already exists and won't be overwritten: {}"
                        ).format(
                            destination.name
                        )
                        self.log_warning(msg, state="end")
                    elif destination in rename_store:
                        msg = (
                            "❗ This destination is already planned from another file: "
                            " {}"
                        ).format(
                            destination.name
                        )
                        self.log_warning(msg, state="end")
                    # Dry run mode just output results without writing anything
                    elif dry_run:
                        msg = "✨ To: {}".format(destination.name)
                        self.log_info(msg, state="end")
                        rename_store.add(destination)
                    # Effective renaming
                    else:
                        msg = "✅ To: {}".format(destination.name)
                        self.log_info(msg, state="end")
                        reverse_store.append(
                            (source, destination)
                        )
                        # Perform renaming
                        source.rename(destination)
                        rename_store.add(destination)
                # If source and destination are identical, nothing to do, just warning
                else:
                    msg = (
                        "❗ Source and destination paths are identical, nothing to "
                        "rename."
                    )
                    self.log_warning(msg, state="end")
        except:
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
                self.log_error("*", dst, "=>", src)
                source.rename(destination, source)
            self.log_error("")

            # Finally raise the original error
            raise

        return {
            "original_store": original_store,
            "rename_store": rename_store,
        }
