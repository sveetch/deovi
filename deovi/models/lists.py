from collections import UserList


class SerializableList(UserList):
    """
    A custom list object that can be used in the chain of model serialization.

    Python builtin list object can not transmit the ``preserve`` option of models
    methods ``as_dict``, so instead models would prefer to use SerializableList as
    model attributes.

    You may expect all the builtin list object behaviors from this custom one.
    """
    def as_dict(self, preserve=False):
        """
        A safe way to convert to a dict without recursion issues.

        Keyword Arguments:
            preserve (bool): If enabled all values which have the method ``as_dict()``
                will use it instead of returning model object. This is almost only
                implemented internally in Deovi models so you can get an output of
                ``as_dict()`` only with Python builtin types.

        Returns:
            dict: This model object attribute serialized in a dictionnary, items named
                after one of names from EXPORT_PRIVATES won't be in the output.
        """
        return [
            (
                v.as_dict(preserve=preserve)
                if preserve is True and hasattr(v, "as_dict")
                else v
            )
            for v in self.data
        ]

    def as_json(self):
        """
        Returns the output of ``as_dict()`` in a JSON string.
        """
        return json.dumps(self.as_dict(), indent=4, cls=ExtendedJsonEncoder)
