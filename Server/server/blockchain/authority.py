# 1- Authority definition
class Authority:
    def __init__(self, authority_id, name):
        self.authority_id = authority_id
        self.name = name

    def to_dict(self):
        return {
            "authority_id": self.authority_id,
            "name": self.name
        }
