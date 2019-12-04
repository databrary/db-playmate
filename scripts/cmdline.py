"""
Simple, interactive command line to use db-playmate.
"""
import toml
from pathlib import Path
import keyring
from db_playmate import Kobo
from db_playmate.box import get_client as get_box_client


def main():
    print("Loading configurations...")
    configs = toml.load(Path("../env/config.toml"))
    kconf = configs.get("kobo")
    bconf = configs.get("box")
    try:
        keyring.delete_password("Box_Auth", "play_box")
        keyring.delete_password("Box_Refresh", "play_box")
    except keyring.errors.PasswordDeleteError:
        pass

    print("Connecting to Box...")
    box = get_box_client(bconf.get("client_id"), bconf.get("client_secret"))
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
    exit(0)


if __name__ == "__main__":
    main()
