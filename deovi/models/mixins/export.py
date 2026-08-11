import json
from dataclasses import fields as dataclasses_fields

from ...utils.jsons import ExtendedJsonEncoder


class ExportMixin:
    """
    Abstract to inherit to include some methods to implement model object export to
    dictionnary or JSON.

    You will need to implement the ``EXPORT_PRIVATES`` attribute: ::

        EXPORT_PRIVATES: ClassVar[list[str]] = [...]

    Its value is a list of field names to ignore from export, commonly used for
    parenting object to avoid recursion error.
    """

    def serialize(self, coerced=False):
        """
        A safe way to convert to a dict without recursion issues.

        Keyword Arguments:
            coerced (bool): If enabled all values with a method ``serialize()``
                will use it instead of returning model object. This is almost only
                implemented internally in Deovi models so you can get an output of
                ``serialize()`` only with Python builtin types.

        Returns:
            dict: This model object attribute serialized in a dictionnary, items named
                after one of names from EXPORT_PRIVATES won't be in the output.
        """
        return {
            f.name: (
                getattr(self, f.name).serialize(coerced=coerced)
                if coerced is True and hasattr(getattr(self, f.name), "serialize")
                else getattr(self, f.name)
            )
            for f in dataclasses_fields(self)
            if f.name not in self.EXPORT_PRIVATES
        }

    def as_coerced(self):
        """
        A shortcut to returns the output of ``serialize()`` with ``coerced`` option
        enabled.
        """
        return self.serialize(coerced=True)

    def as_json(self):
        """
        Returns the output of ``serialize()`` in a JSON string.
        """
        return json.dumps(self.serialize(), indent=4, cls=ExtendedJsonEncoder)
