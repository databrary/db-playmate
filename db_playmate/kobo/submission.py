from more_itertools import first


class Submission:
    """Wrapper for a dictionary of answers."""

    @classmethod
    def ignore_key(cls, key):
        return any(key.startswith(x) for x in ("_", "meta"))

    def __init__(self, data, version=None):
        self.version = version
        self.data = {}
        for key, value in data.items():
            if self.ignore_key(key):
                continue

            qid = key.split("/")[-1]
            if not qid:
                raise Exception(f"Invalid key: {key}")
            self.data[qid] = value

    def to_row_dict(self, questions):
        return {str(q): self.answer(q) for q in questions}

    def answer(self, question):
        return first([self.data.get(name) for name in question.names.values()])
