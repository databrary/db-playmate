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
        return self.names[self.__sid] or str(self.__sid)


class QuestionGroup:
    """
    A group of related questions.
    """

    def __init__(self, group_id, *questions):
        self.group_id = group_id
        self.questions = list(questions)

    def add_questions(self, question):
        self.questions.append(question)

    def __sizeof__(self):
        return len(self.questions)
