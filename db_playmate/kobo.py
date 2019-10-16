import toml
import requests


class Kobo:
    def get_forms(self, url, token):
        response = requests.get(
            url,
            params={"format": "json"},
            headers={
                "Authorization": f"Token {token}",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        return response.json()
