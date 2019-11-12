import requests
from furl import furl
from requests import HTTPError

from db_playmate.koboform import KoboForm


class Kobo:
    """Object to interface with the KoboToolbox API."""

    def __init__(self, base_url, token):
        """Create a new KoboToolbox API interface"""
        self.base_url, self.token = base_url, token
        self.params = {"format": "json"}
        self.headers = {
            "Authorization": f"Token {self.token}",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Accept": "application/json",
        }
        self.forms = dict()
        self._response = {}
        self.get_forms(update=True)

    def get_forms(self, update=False):
        """Sends query for forms if update is true or forms haven't been fetched yet.
            Returns self.
        """
        if update or not self.forms:
            try:
                url = furl(self.base_url)
                url.path.add("assets")
                response = requests.get(
                    url=url.url, params=self.params, headers=self.headers
                )
                response.raise_for_status()
            except HTTPError as http_err:
                print(f"HTTP error: {http_err}")
                raise http_err
            except Exception as err:
                raise err
            else:
                rj = response.json()
                self._response = rj
                for data in rj["results"]:
                    form = KoboForm(data)
                    self.forms[form.id] = form

        return self

    def get_form(self, form_id, update=False):
        if update or form_id not in self.forms.keys():
            try:
                url = furl(self.base_url)
                url.path.add("assets", str(form_id), "submissions")
                response = requests.get(
                    url=url.url, params=self.params, headers=self.headers
                )
                response.raise_for_status()
            except HTTPError as http_err:
                print(f"HTTP error: {http_err}")
            except Exception as err:
                raise err
            else:
                rj = response.json()
                for submission in rj:
                    self.forms[form_id].add_submission(submission)

        return self.forms[form_id]
