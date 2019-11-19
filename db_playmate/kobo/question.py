class Question:
    """Stores information about a form question; essentially sets of Kobo ids and question texts."""

    def __init__(self, qid, text="", label=None):
        self.sigs = {qid: text}
        self.label = label
        self.__sid = qid

    def congruent_to(self, other):
        """Two questions are equivalent if they share any common ids."""

        return any(self.sigs.keys() & other.sigs.keys())

    def merge(self, other, replace_label=False, replace=False):
        """
        Adds signatures from other to self
        :param other: other question
        :param replace_label: replaces self's label wither other's iff True
        :param replace: if true, overwrites values in self for duplicate keys in sigs
        :return: self
        """
        for ok, ov in other.sigs.items():
            if ok in self.sigs.keys() and not replace:
                continue

            self.sigs[ok] = ov

        if replace_label:
            self.label = other.label

        return self

    def __str__(self):
        return self.sigs[self.__sid] if self.label is None else self.label
