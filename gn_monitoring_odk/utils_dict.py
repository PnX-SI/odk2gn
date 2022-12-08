from functools import reduce


class NestedDictAccessor(dict):
    # def __init__(self, *args, **kwargs):
    #     print("LAAAA", args)
    #     super().__init__(*args, **kwargs)

    def get_nested(self, key, separator="/"):
        return reduce(
            lambda val, key: val.get(key) if val else None, key.split(separator), self
        )


test = NestedDictAccessor({"Gfg": {"is": "best"}})
