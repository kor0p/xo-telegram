import json

class JSON(dict):

    @classmethod
    def loads(cls, value):
        return JSON(json.loads(value))

    def __getattr__(self, key):
        if key in dir(self):
            return super().__getattribute__(key)
        result = self.get(key)
        if isinstance(result, dict):
            return JSON(result)
        if isinstance(result, list) and len(result) and isinstance(result[0], dict):
            return [JSON(value) for value in result]
        return result

    def __setattr__(self, key, value):
        if key in dir(self):
            return super().__setattr__(key, value)
        self[key] = value

    def __delattr__(self, key):
        if self.get(key) is not None:
            return self.pop(key)
