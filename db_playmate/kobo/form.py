import csv

from furl import furl

from .question import Question
from .submission import Submission


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
        self.data = data
        self._parse_summary()
        self._parse_survey()

        self._subs_raw = {}
        self.submissions = []
        self.connection = connection

    def _parse_summary(self):
        try:
            self.num_columns = self.data["summary"]["row_count"]
        except (KeyError, AttributeError):
            self.num_columns = None
        self.url = self.data.get("url")
        self.id = self.data.get("uid")
        self.name = self.data.get("name")
        self.type = self.data.get("asset_type")
        self.current_version = self.data.get("version_id")
        self.num_submissions = self.data.get("deployment__submission_count")

    def _parse_survey(self):
        self.questions = []
        if self.data is None:
            return

        # Parse survey questions
        content = self.data.get("content")
        if content is not None:
            survey = content.get("survey")
            if survey is not None:
                self._parse_survey(survey)
        qs = filter(None, [self.parse_question(q) for q in survey])
        self.questions.extend(qs)

    def parse_question(self, question):
        qtype = question.get("type")
        if qtype is None or qtype in self.ignored_qtypes:
            return None

        qid = question.get("$kuid")
        name = question.get("name")
        try:
            label = question.get("label")[0]
        except (KeyError, TypeError):
            label = ""
        self.questions.append(Question(qid=qid, name=name, label=label, qtype=qtype))

    def parse_group(self, group):
        """
        Parse a group of questions and set a group identifier
        :param group:
        :return:
        """

    def add_submission(self, data):
        """
        Parse submission responses and add to self.submissions.
        :param data: dict with question id and answers
        :return: submission object mapping questions to answers
        """
        self.submissions.append(Submission(data=data))

    def _submission_url(self):
        url = furl(self.url)
        url.path.add("submissions")
        return url.url

    def get_submissions(self):
        rj = self.connection.send_query(url=self._submission_url()).json()
        self._subs_raw = rj
        for data in rj:
            self.add_submission(data)

    def to_csv(self, file):
        writer = csv.DictWriter(
            file, [str(q) for q in self.questions], dialect=csv.unix_dialect
        )
        writer.writeheader()
        writer.writerows([s.to_row_dict(self.questions) for s in self.submissions])
