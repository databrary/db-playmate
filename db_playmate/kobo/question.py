class Question:
    """Stores information about a form question; essentially sets of Kobo ids and question texts."""

    def __init__(self, qid, name, label=None, qtype=None):
        self.names = {qid: name}
        self.labels = {qid: label}
        self.qtype = qtype
        self.__sid = qid

    def add_alias(self, qid, name, label=None):
        self.names[qid] = name
        self.labels[qid] = label

    def __str__(self):
        return self.names[self.__sid]
