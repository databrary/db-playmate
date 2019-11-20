import csv

from furl import furl

from .question import Question


class Form:
    """
    Stores information about a particular form.
        * set of questions
        * collection of answers mapped to questions (submissions)
        * forms can have any number of variations on questions; submissions are particular versions of a form and need
          not contain answers to all questions across all version
    Provides csv representation.
        * each submission is a row of data
        * each question is a column
        * default value for questions not in particular submissions
    """

    ignored_qtypes = [
        "calculate",
        "note",
        "begin_group",
        "end_group",
        "begin_repeat",
        "end_repeat",
    ]

    def __init__(self, data, connection=None):
        self.raw_data = data
        self.questions = []

        # Parse survey questions
        if "content" in data.keys():
            if "survey" in data.get("content").keys():
                self.parse_survey(data.get("content").get("survey"))

        self._subs_raw = {}
        self.submissions = []
        self.connection = connection

        try:
            self.num_columns = data["summary"]["row_count"]
        except [KeyError, AttributeError]:
            self.num_columns = None
        self.url = data["url"]
        self.id = data["uid"]
        self.name = data["name"]
        self.type = data["asset_type"]
        self.current_version = data["version_id"]
        self.num_submissions = data["deployment__submission_count"]

    def parse_survey(self, survey):
        for q in survey:
            qid = q.get("$kuid")
            qtype = q.get("type")
            label = q.get("label")
            name = q.get("name")

            if qid is None:
                continue
            if qtype in self.ignored_qtypes:
                continue

            if label:
                label = label[0]
            self.questions.append(Question(qid=qid, name=name, label=label))

    def __call__(self, *args, **kwargs):
        for data in args:
            self.add_submission(self.__parse_sub(data))

    def __parse_sub(self, data):
        pass

    def add_submission(self, data):
        """
        Parse submission responses and add to self.submissions.
        :param data: dict with question id and answers
        :return: submission object mapping questions to answers
        """
        pass

    def _submission_url(self):
        url = furl(self.url)
        url.path.add("submissions")
        return url.url

    def get_submissions(self, headers, params):
        rj = self.connection.send_query(url=self._submission_url()).json()
        self._subs_raw = rj
        for data in rj:
            self.add_submission(data)

    def to_csv(self, file):
        with open(file) as f:
            writer = csv.DictWriter(f, map(str, self.questions))
            writer.writeheader()
            writer.writerows(map(str, self.questions))
            writer.writerow(
                [s.get(q) for s in self.submissions for q in self.questions]
            )
