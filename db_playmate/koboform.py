class KoboForm:
    """Stores information about a particular form."""

    def __init__(self, data):
        self.raw_data = data
        self.__parse()
        self.submissions = []

    def __parse(self):
        """Unwrap dict representation of a form."""

        self.num_columns = self.raw_data["summary"]["row_count"]
        self.id = self.raw_data["uid"]
        self.name = self.raw_data["name"]
        self.type = self.raw_data["asset_type"]
        self.version_id = self.raw_data["version_id"]
        self.num_submissions = self.raw_data["deployment__submission_count"]

    def add_submission(self, data):
        """
        Parse submission responses and add to self.submissions.
        :param data:
        :return:
        """
        pass

    def to_csv(self):
        pass


class Question:
    """Stores information about a form question; essentially sets of Kobo ids and question texts."""

    def __init__(self, qid, text=""):
        self.ids = set(qid)
        self.texts = set(text)

    def __eq__(self, other):
        """Two questions are equivalent if they share any common ids."""
        self.ids.intersection(other.ids)

    def merge(self, other):
        self.ids.update(other.ids)
        self.texts.update(other.texts)


class Submission:
    """Wrapper for a dictionary mapping questions to answers."""

    def __init__(self):
        self.answers = {}
