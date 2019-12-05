"""
Simple, interactive command line to use db-playmate.
"""
from argparse import ArgumentParser
import toml
from pathlib import Path
import keyring
from db_playmate import Kobo
from db_playmate.box import get_client as get_box_client


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--config-file",
        "-c",
        required=True,
        help="toml file with Box and KoboToolbox credentials",
    )
    args = parser.parse_args()
    config_path = Path(args.config_file).resolve()
    print(f"Loading configurations from {config_path}...")
    try:
        configs = toml.load(config_path)
    except FileNotFoundError:
        print("ERROR: failed to load configurations")
        return 1

    kconf = configs.get("kobo")
    bconf = configs.get("box")
    try:
        keyring.delete_password("Box_Auth", "play_box")
        keyring.delete_password("Box_Refresh", "play_box")
    except keyring.errors.PasswordDeleteError:
        pass

    print("Connecting to Box...")
    client_id = bconf.get("client_id")
    client_secret = bconf.get("client_secret")
    try:
        box = get_box_client(client_id, client_secret)
    except Exception as e:
        print("ERROR: failed to initialize box client. See error message.")
        print(e)
        return 1

    box.create_folder("", "kobo")

    print("Connecting to KoboToolbox...")
    kobo = Kobo(base_url=kconf.get("base_url"), token=kconf.get("auth_token"))
    src_folder = Path("../env/kobo")
    src_folder.mkdir(parents=False, exist_ok=True)
    for form in kobo.get_forms().values():
        print(f"{form.name}: {form.num_submissions} submissions. Downloading...")
        filename = form.name + ".csv"
        with open(filename, "w+") as outfile:
            form.to_csv(outfile)
        print("Uploading to Box...")
        box.upload_file(filename, "kobo")

    print("Finished.")
    return 0


if __name__ == "__main__":
    exit(main())
