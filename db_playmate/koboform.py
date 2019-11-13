import csv
import logging as log

import requests
from furl import furl
from requests import HTTPError


class KoboForm:
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

    def __init__(self, data):
        self.raw_data = data
        self.questions = []
        self.__parse()
        self._subs_raw = {}
        self.submissions = []

    def __parse(self, max_repeats=10):
        """Unwrap dict representation of a form."""
        # TODO: what to do about repeated questions??

        summary = self.raw_data["summary"]
        self.num_columns = summary["row_count"] if summary else None
        self.url = self.raw_data["url"]
        self.id = self.raw_data["uid"]
        self.name = self.raw_data["name"]
        self.type = self.raw_data["asset_type"]
        self.current_version = self.raw_data["version_id"]
        self.num_submissions = self.raw_data["deployment__submission_count"]

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
        try:
            response = requests.get(
                url=self._submission_url(), params=params, header=headers
            )
            response.raise_for_status()
        except HTTPError as http_err:
            log.error(f"HTTP error: {http_err}")
            raise http_err
        except Exception as err:
            raise err
        else:
            rj = response.json()
            self._subs_raw = rj
            for data in rj:
                self.add_submission(data)

    def to_csv(self, file):
        with open(file) as f:
            writer = csv.DictWriter(f, map(str, self.questions))
            writer.writerows([])
            for s in self.submissions:
                writer.writerow([s.get(q) for q in self.questions])


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
        return self

    def __add__(self, other):
        return self.merge(other)


class Submission:
    """Wrapper for a dictionary mapping questions to answers."""

    def __init__(self, version=None):
        self.answers = {}
        self.version = version
