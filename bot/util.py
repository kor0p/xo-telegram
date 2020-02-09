class JSON:
    def __init__(self, **value):
        self.value = value

    def __getattr__(self, key):
        if key in ['value']:
            return super().__getattribute__(key)
        return self.value[key]
