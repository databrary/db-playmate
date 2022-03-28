import requests
from requests import HTTPError
from .form import Form
from typing import List
from db_playmate import app


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
        self.forms = {}
        self._response = {}
        self.get_forms(update=True)

    def get_forms(self, update=False) -> List[Form]:
        """
        Sends query for forms if update is true or forms haven't been fetched yet.
        :param update: Set true to force an http request to kobo server
        :return: available forms
        """
        if update or not self.forms:
            url = self.base_url
            url += "/assets"
            response = self.send_query(url)
            rj = response.json()
            self._response = rj
            for data in rj["results"]:
                if data.get("asset_type") != "survey":
                    continue

                form = Form(data, connection=self)
                self.forms[form.id] = form

        return self.forms

    def get_form(self, form_id, update=False):
        if update or form_id not in self.forms.keys():
            url = self.base_url

            url += "/assets/" + str(form_id)
            rj = self.send_query(url).json()
            self.forms[form_id] = Form(rj, self)

        return self.forms[form_id]

    def send_query(self, url, **headers):
        hds = {**self.headers, **headers}
        try:
            response = requests.get(url=url, params=self.params, headers=hds)
            response.raise_for_status()
        except HTTPError as http_err:
            app.logger.error(f"HTTP error: {http_err}")
        except Exception as err:
            raise err
        else:
            return response
