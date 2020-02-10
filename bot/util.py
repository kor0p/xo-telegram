class JSON:
    def __init__(self, **value):
        self.value = value

    def __len__(self):
        return 0

    def __getattr__(self, key):
        if key in ['value', '__len__']:
            return super().__getattribute__(key)
        return self.value[key]
