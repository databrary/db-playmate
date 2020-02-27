"""
Simple, interactive command line to use db-playmate.
"""
from argparse import ArgumentParser
import toml
from pathlib import Path
import keyring
from db_playmate import Kobo
from db_playmate.box import get_client as get_box_client
import tempfile
import csv


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--config-file",
        "-c",
        required=False,
        help="toml file with Box and KoboToolbox credentials",
    )
    args = parser.parse_args()
    if args.config_file is None:
        args.config_file = "config.toml"
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

    # box.create_folder("", "kobo")

    print("Connecting to KoboToolbox...")
    kobo = Kobo(base_url=kconf.get("base_url"), token=kconf.get("auth_token"))
    src_folder = Path("./kobo")
    src_folder.mkdir(parents=False, exist_ok=True)
    dest_folder = "kobo"
    for frm in kobo.get_forms().values():
        print(f"{frm.name}: {frm.num_submissions} submissions. Downloading...")
        filename = frm.name + ".csv"
        with open(Path(src_folder, filename), "w+") as outfile:
            frm.to_csv(outfile)

        print("Uploading to Box...")
        groups = frm.group_by("site_id")
        for site, subms in groups.items():
            print(f"\t- Uploading {len(subms)} submissions for {site}")
            # write data to temp file
            tf, tp = tempfile.mkstemp()
            with open(tf, "w", newline="") as tmp:
                w = csv.DictWriter(
                    tmp, [str(q) for q in frm.questions], dialect=csv.unix_dialect
                )
                w.writeheader()
                w.writerows([s.as_dict() for s in subms])

            # upload to box
            site_folder = str(Path(dest_folder, site))
            box.create_folders(site_folder)
            box.upload_file(tp, site_folder, new_name=filename)
            del tf

    print("Finished.")
    return 0


if __name__ == "__main__":
    exit(main())
