import requests
from requests import HTTPError

from db_playmate.koboform import KoboForm


class Kobo:
    """Object to interface with the KoboToolbox API."""

    def __init__(self, base_url, token):
        """Create a new KoboToolbox API interface"""
        self.base_url, self.token = base_url, token
        self.forms = []
        self.__get_forms(update=True)

    def __get_forms(self, update=False):
        """Sends query for forms if update is true or forms haven't been fetched yet.
            Returns self.
        """
        if update or not self.forms:
            try:
                response = requests.get(
                    self.base_url,
                    params={"format": "json"},
                    headers={
                        "Authorization": f"Token {self.token}",
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Accept": "application/json",
                    },
                )
                response.raise_for_status()
            except HTTPError as http_err:
                print(f"HTTP error: {http_err}")
                raise http_err
            except Exception as err:
                raise err
            else:
                rj = response.json()
                self.forms.extend(map(KoboForm, rj["results"]))

        return self

    def form_by_id(self, id):
        if not self.forms:
            raise AttributeError
