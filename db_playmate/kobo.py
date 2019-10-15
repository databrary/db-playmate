import toml
import requests


def get_forms(url, token):
    response = requests.get(
        url,
        params={"format": "json"},
        headers={
            "Authorization": f"Token {token}",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
    return response


def main(config):
    r = get_forms(url=config["base_url"], token=config["auth_token"])
    print(r.json())


if __name__ == "__main__":
    try:
        cf = open("../env/config.toml")
    except:
        cf = open("../config.toml")

    with cf:
        config = toml.load(cf)
        kobo_config = config["kobo"]
        main(kobo_config)
