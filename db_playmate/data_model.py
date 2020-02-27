import pickle
import re


class Submission:
    def __init__(self, site_id, subj_number, db_asset):
        self.asset = db_asset
        self.vol_id = db_asset["vol_id"]
        self.site_id = site_id
        self.subj_number = subj_number
        self.kobo_data = None
        self.ready_for_qa = False
        self.ready_for_coding = False
        self.moved_to_silver = False
        self.assigned_coding_site = None
        self.primary_coding_finished = False
        self.ready_for_rel = False
        self.rel_coding_finished = False
        self.moved_to_gold = False
        self.id = "{} - {} - {}".format(self.vol_id, self.site_id, self.subj_number)
        self.name = self.id  # TODO For now, revisit this

        # Lists because there can be multiple videos per
        # task
        self.natural_play = []
        self.house_walk = []
        self.home_question = []
        self.structured_play = []
        self.consent = []

        self.video_map = {
            "NaturalPlay": self.natural_play,
            "StructuredPlay": self.structured_play,
            "HouseWalkthrough": self.house_walk,
            "Questionnaires": self.home_question,
            "Consent": self.consent,
        }

    def _to_csv(self):
        # Return a CSV string rep
        pass

    def __eq__(self, other):
        if self.vol_id == other.vol_id and self.filename == other.filename:
            return True
        else:
            return False

    def __str__(self):
        filenames = [x["filename"] for a in self.video_map.values() for x in a]
        return "Asset: {} {} {} - Filenames: ".format(
            self.vol_id, self.site_id, self.subj_number
        ) + " ".join(filenames)

    def add_video(self, asset):
        filename = asset["filename"]
        video_type = filename.split("_")[-1].split(".")[0]
        if video_type[-1].isdigit():
            video_type = video_type[:-1]
        if video_type in self.video_map and asset not in self.video_map.values():
            print(video_type)
            self.video_map[video_type].append(asset)
        else:
            print(
                "Warning: Could not find video_type",
                video_type,
                "in map or video was already in list",
            )


class Lab:
    def __init__(self, site_code, lab_code, pi_fullname, email, institution):
        self.site_code = site_code
        self.lab_code = lab_code
        self.pi_fullname = pi_fullname
        self.email = email
        self.db_volume = "PLAYProject_" + site_code
        self.institution = institution
        self.vol_id = None

    def __str__(self):
        return "{} - {}".format(institution, site_code)

    def assign_video(self, asset):
        pass


class Site:
    def __init__(self, site_code):
        self.site_code = site_code
        self.db_volume = "PLAYProject_" + site_code
        self.submissions = {}
        self.labs = {}

    def add_video(self, site_id, asset):
        filename = asset["filename"]
        subj_number = filename.split("_")[2]
        if subj_number not in self.submissions:
            self.submissions[subj_number] = Submission(site_id, subj_number, asset)
        self.submissions[subj_number].add_video(asset)

    def get_vol_id(self, databrary_instance):
        self.vol_id = databrary_instance.get_volume_by_name(self.db_volume)


class Datastore:
    def __init__(self):
        self.labs = {}  # lab_code -> lab
        self.sites = {}  # site_code -> site

    def add_video(self, asset):
        site_id = asset["filename"].split("_")[1].strip()
        self.sites[site_id].add_video(site_id, asset)

    def save(self, filename):
        with open(filename, "wb") as handle:
            pickle.dump(self, handle)

    def get_submissions(self):
        subs = []
        for s in self.sites.values():
            for v in s.submissions.values():
                subs.append(v)
        return subs

    def find_submission(self, sub_id):
        for s in self.get_submissions():
            if s.id == sub_id:
                return s
        return None

    def find_lab(self, lab_id):
        for s in self.labs:
            if lab_id == s.lab_code:
                return s
        return None
