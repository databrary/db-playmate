class Question:
    """Represents a particular question on a form"""

    def __init__(self, qid, name, label=None, qtype=None):
        self.names = {qid: name}
        self.labels = {qid: label}
        self.qtype = qtype
        self.__sid = qid

    def add_alias(self, qid, name, label=None):
        self.names[qid] = name
        self.labels[qid] = label

    def is_alias(self, other) -> bool:
        if isinstance(other, int):
            return other in self.names
        elif isinstance(other, self.__class__):
            return len(self.names & other.names) > 0
        else:
            raise NotImplemented

    def __str__(self):
        return self.names[self.__sid] or str(self.__sid)

    def __hash__(self):
        return hash(self)
