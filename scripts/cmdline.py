"""
Simple, interactive command line to use db-playmate.
"""
import toml
from pathlib import Path
from db_playmate import Kobo, Box


def main():
    print("Loading configurations...")
    configs = toml.load(Path("../env/config.toml"))
    kconf = configs.get("kobo")
    bconf = configs.get("box")

    print("Connecting to Box...")
    box = Box(bconf.get("client_id"), bconf.get("client_secret"))
    if "kobo" not in [f.get_name() for f in box.get_root().get_items()]:
        dest_folder = box.create_folder(box.get_root(), "kobo")
    else:
        dest_folder = box.get_folder("kobo")

    print("Connecting to KoboToolbox...")
    kobo = Kobo(base_url=kconf.get("base_url"), token=kconf.get("auth_token"))
    src_folder = Path("../env/kobo")
    src_folder.mkdir(parents=False, exist_ok=True)
    for form in kobo.get_forms():
        print(f"{form.name}: {form.num_submissions} submissions. Downloading...")
        filename = form.name + ".csv"
        with open(filename) as outfile:
            form.to_csv(outfile)
        print("Uploading to Box...")
        box.upload_file(filename, dest_folder)


if __name__ == "__main__":
    main()
