import csv
from furl import furl
from .question import Question
from .submission import Submission
import logging as log


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
        self.questions = list()

        self._subs_raw = {}
        self.submissions = []
        self.connection = connection

        self._parse_summary()

        # Check if survey contents are present. If not, fetch.
        self.content = data.get("content")
        if self.content is None:
            self.get_form_contents()

        # Parse form contents
        self._parse_survey()

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

    def get_form_contents(self, url=None):
        if self.connection is None:
            raise AttributeError("Missing connection object.")

        if url is None and self.url is None:
            raise AttributeError("Missing url.")

        if not url:
            url = self.url

        rj = self.connection.send_query(url).json()
        if rj is None:
            log.info("Failed to get form contents.")
            return

        self.content = rj.get("content")

    def _parse_survey(self):
        if self.content is None:
            raise AttributeError("Not form contents found.")

        survey = self.content.get("survey")
        if survey is None:
            raise AttributeError("No survey in form contents.")

        qs = filter(None, [self.parse_item(q) for q in survey])
        self.questions.extend(qs)

    def parse_item(self, item):
        qtype = item.get("type")
        if qtype is None or qtype in self.ignored_qtypes:
            return None

        qid = item.get("$kuid")
        name = item.get("name")
        try:
            label = item.get("label")[0]
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

        return self.submissions

    def to_csv(self, file):
        if len(self.submissions) < self.num_submissions:
            self.get_submissions()

        writer = csv.DictWriter(
            file, [str(q) for q in self.questions], dialect=csv.unix_dialect
        )
        writer.writeheader()
        writer.writerows([s.to_row_dict(self.questions) for s in self.submissions])
