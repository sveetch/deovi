# -*- coding: utf-8 -*-
"""
Exceptions
==========

Specific application exceptions.
"""


class DeoviClientBaseException(Exception):
    """
    Exception base.

    You should never use it directly except for test purpose. Instead make or
    use a dedicated exception related to the error context.
    """
    pass


class DummyError(DeoviClientBaseException):
    """
    Dummy exception sample to raise from your code.
    """
    pass


class TaskValidationError(DeoviClientBaseException):
    """
    When task rules are not valid.
    """
    pass


class CollectorError(DeoviClientBaseException):
    """
    For any media file collector error.
    """
    pass


class JobValidationError(DeoviClientBaseException):
    """
    When a job is not valid.

    Keyword Arguments:
        validation_details (dict): A possible dictionnary of validation details. It
            won't output as exception message from traceback, you need to exploit it
            yourself if needed.
    """
    def __init__(self, *args, **kwargs):
        self.validation_details = kwargs.pop("validation_details", None)
        super().__init__(*args, **kwargs)
