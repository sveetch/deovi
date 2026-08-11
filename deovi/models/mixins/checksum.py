from ...utils.checksum import checksum_file_content, checksum_content


class ChecksumMixin:
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
