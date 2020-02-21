import os
import pickle
from flask import Flask, render_template
from sheets import read_master
from data_model import Datastore, Submission
from bridge import Bridge

SAVE_FILE = "env/db_playmate.pickle"


def check_for_new():
    # Check Kobo for a list of new files that need to be sent to QA
    pass


def get_labs(bridge):
    sites, labs = read_master()
    for site in sites.values():
        site.get_vol_id(bridge.db)
    return sites, labs


def get_submissions(sites, bridge, datastore):
    for site in sites.values():
        assets = bridge.db.get_assets_for_volume(site.vol_id)
        if assets is not None:
            for a in assets:
                print(a)
                if a['filename'].endswith(".mp4"):
                    try:
                        datastore.add_video(a)
                        print("FOUND VIDEO!", a)
                    except IndexError as e:
                        print("Error adding video")
                        print(e)


def get_kobo_forms(bridge):
    bridge.transfer_kobo_to_box()


def startup():
    # Set up the Flask server we'll be using

    # Set up the DB/Box/Kobo bridge
    bridge = Bridge("env/config.toml")

    # Load the data if it exists, otherwise populate from
    # online resources
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'rb') as handle:
            datastore = pickle.load(handle)
    else:
        datastore = Datastore()
        datastore.sites, datastore.labs = get_labs(bridge)
        get_submissions(datastore.sites, bridge, datastore)

        print(datastore.sites.keys())
        #get_kobo_forms(bridge)
        datastore.save(SAVE_FILE)

        for site_code in datastore.sites:
            print(datastore.sites[site_code].submissions.keys())
            for subj in datastore.sites[site_code].submissions:
                print(site_code, subj, datastore.sites[site_code].submissions[subj])


if __name__ == "__main__":
    startup()
