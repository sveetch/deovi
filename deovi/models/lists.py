from collections import UserList

from .mixins.export import ExportMixin


class SerializableList(ExportMixin, UserList):
    """
    A custom list object that can be used in the chain of model serialization.

    Python builtin list object can not transmit the ``coerced`` option of models
    methods ``serialize``, so instead models would prefer to use SerializableList as
    model attributes.

    You may expect all the builtin list object behaviors from this custom one with
    addition of the serialization methods.
    """
    def serialize(self, coerced=False):
        """
        A safe way to convert to a dict without recursion issues.

        Keyword Arguments:
            coerced (bool): If enabled all values which have the method ``serialize()``
                will use it instead of returning model object. This is almost only
                implemented internally in Deovi models so you can get an output of
                ``serialize()`` only with Python builtin types.

        Returns:
            dict: This model object attribute serialized in a dictionnary, items named
                after one of names from EXPORT_PRIVATES won't be in the output.
        """
        return [
            (
                v.serialize(coerced=coerced)
                if coerced is True and hasattr(v, "serialize")
                else v
            )
            for v in self.data
        ]
