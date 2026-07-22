import json
from dataclasses import fields as dataclasses_fields

from ..utils.jsons import ExtendedJsonEncoder
from ..utils.checksum import checksum_file_content, checksum_content


class ChecksumAbstract:
    """
    Abstract to inherit to include some methods to implement checksum in a model.

    You still need to implement the required fields: ::

        checksum: str = None
        autochecksum: InitVar[bool] = False
        CHECKSUM_FIELD: ClassVar[str] = "source"

    Where ``CHECKSUM_FIELD`` is the field name for the file to checksum.

    And its initialization in ``Model.__post_init__`` method: ::

        def __post_init__(self, ..., autochecksum):
            ...

            if autochecksum:
                self.set_checksum()

    This a recommended sample, you may however implement in another way.
    """
    def get_file_checksum(self):
        """
        Returns the checksum of the file content.
        """
        return checksum_file_content(getattr(self, self.CHECKSUM_FIELD))

    def get_content_checksum(self, content):
        """
        Returns the checksum of given content string.
        """
        return checksum_content(content)

    def set_checksum(self):
        """
        Build the checksum of the file content and set it onto object attribute.
        """
        self.checksum = self.get_file_checksum()

        return self.checksum


class ExportAbstract:
    """
    Abstract to inherit to include some methods to implement model object export to
    dictionnary or JSON.

    You will need to implement the ``EXPORT_PRIVATES`` attribute: ::

        EXPORT_PRIVATES: ClassVar[list[str]] = [...]

    Its value is a list of field names to ignore from export, commonly used for
    parenting object to avoid recursion error.
    """

    def as_dict(self, preserve=False):
        """
        A safe way to convert to a dict without recursion issues.

        Keyword Arguments:
            preserve (bool): If enabled all values which have the method ``as_dict()``
                will use it instead of returning their object. This is almost only
                implemented internally in Deovi models so you can get an output of
                ``as_dict()`` only with Python builtin types.

        Returns:
            dict: This model object attribute serialized in a dictionnary, items named
                after one of names from EXPORT_PRIVATES won't be in the output.
        """
        return {
            f.name: (
                getattr(self, f.name).as_dict(preserve=preserve)
                if preserve is True and hasattr(getattr(self, f.name), "as_dict")
                else getattr(self, f.name)
            )
            for f in dataclasses_fields(self)
            if f.name not in self.EXPORT_PRIVATES
        }

    def as_json(self):
        """
        Returns the output of ``as_dict()`` in a JSON string.
        """
        return json.dumps(self.as_dict(), indent=4, cls=ExtendedJsonEncoder)
