from ..exceptions import JobValidationError, TaskValidationError

from .printer import PrinterInterface
from .jobs import Job
from .validators import validate_jobs, validate_task_options


class JobRunner(PrinterInterface):
    """
    Validate then run Jobs.

    Arguments:
        task_class (tasks.TaskMaster): The task manager class to instanciate for each
            Job.
    """
    def __init__(self, task_class):
        super().__init__()

        self.task_class = task_class
        self.task_infos = None

    def get_available_tasks(self):
        """
        Get tasks informations (name and requirements) with inspection on task methods.

        Returns:
            dict: Dictionnary of tasks indexed on their name (the method name without
            suffix ``task_``) and with required attribute as value.
        """
        tasks = {}

        for item in dir(self.task_class):
            if item.startswith("task_"):
                name = item[len("task_"):]
                tasks[name] = []

                method = getattr(self.task_class, item)

                if hasattr(method, "required"):
                    tasks[name] = method.required

        return tasks

    def get_jobs(self, filepaths):
        """
        Load, inspect and validate every given Job filepaths.

        Validation is in two parts:

        1. Validate job parameters;
        2. Validate jobs tasks.

        The first one blocks the second one since invalid job parameters may not be
        suitable to open/parse for tasks.

        Arguments:
            filepaths (list): List of Path objects for job files.

        Raises:
            JobValidationError: If there is any error during job validation. The
                exception will contains the full detail of errors in
                ``validation_details`` attribute.

        Returns:
            list: List of Job model instances.
        """
        task_infos = self.get_available_tasks()
        job_errors = validate_jobs(filepaths)

        # If there is any error, stop execution with an exception resuming errors from
        # all invalid jobs
        if job_errors:
            raise JobValidationError(
                "Error(s) occured during job(s) validation",
                validation_details=job_errors,
            )

        # Load every job files in models
        jobs = [Job.load(item) for item in filepaths]

        # Validate tasks from all jobs
        task_by_job_errors = {}
        for job in jobs:
            job_source = str(job.source)

            # Check every job tasks
            for task_name, task_options in job.tasks:
                # First check job file exists else store error but dont continue to
                # task
                if task_name not in task_infos:
                    if job_source not in task_by_job_errors:
                        task_by_job_errors[job_source] = []
                    task_by_job_errors[job_source].append(
                        "There is no task with name '{}'.".format(task_name)
                    )
                    continue

                # Finally validate job tasks
                try:
                    validate_task_options(
                        task_name,
                        task_infos[task_name],
                        **task_options
                    )
                except TaskValidationError as e:
                    if job_source not in task_by_job_errors:
                        task_by_job_errors[job_source] = []
                    task_by_job_errors[job_source].append(str(e))

        # Raise exception with all task errors if any
        if task_by_job_errors:
            raise JobValidationError(
                "Error(s) occured during job(s) task(s) validation",
                validation_details=task_by_job_errors,
            )

        return jobs

    def run(self, filepaths, dry_run=True):
        """
        Run jobs from all given job filepaths.

        Arguments:
            filepaths (list): List of Path objects for job files.

        Keyword Arguments:
            dry_run (boolean): To enable "dry run" mode which does not write anything.
                If disabled, every renaming will be writed to the filesystem. Disabled
                by default.
        """
        task_manager = self.task_class()

        jobs = self.get_jobs(filepaths)

        # Perform all tasks from each jobs
        for job in jobs:
            job.run(task_manager, dry_run=dry_run)
