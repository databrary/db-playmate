from more_itertools import first


class Submission:
    """
    A mapping of questions to answers
    """

    @classmethod
    def ignore_key(cls, key):
        return any(key.startswith(x) for x in ("_", "meta"))

    def __init__(self, parent, data, version=None, default_value=""):
        self.version = version
        self.default_value = default_value
        self.data = {}
        self.parent = parent
        for key, value in data.items():
            if self.ignore_key(key):
                continue

            qid = key.split("/")[-1]
            if not qid:
                raise Exception(f"Invalid key: {key}")
            self.data[qid] = value

    def as_dict(self):
        return {str(q): self.answer(q) for q in self.parent.questions}

    def answer(self, question):
        ans = first([self.data.get(name) for name in question.names.values()])
        return ans or self.default_value

    def as_csv(self):
        return ",".join(self.answer(q) for q in self.parent.questions)

    def __repr__(self):
        return self.as_csv()
