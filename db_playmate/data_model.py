import pickle
import db_playmate.constants as constants


class Submission:
    def __init__(self, site_id, subj_number, db_asset):
        self.asset = db_asset
        self.asset_id = db_asset["id"]
        self.slot_id = db_asset["slot_id"]
        self.birthdate = db_asset["birthdate"] if "birthdate" in db_asset else ""
        self.gender = db_asset["gender"] if "gender" in db_asset else ""
        self.testdate = db_asset["testdate"] if "testdate" in db_asset else ""
        self.language = db_asset["language"] if "language" in db_asset else ""
        self.permission = db_asset["permission"]
        self.vol_id = db_asset["vol_id"]
        self.site_id = site_id
        self.subj_number = subj_number
        self.kobo_data = None
        self.ready_for_qa = False
        self.ready_for_coding = False
        self.moved_to_silver = False
        self.assigned_coding_site_tra = None
        self.assigned_coding_site_com = None
        self.assigned_coding_site_emo = None
        self.assigned_coding_site_loc = None
        self.assigned_coding_site_obj = None
        self.primary_coding_finished_tra = False
        self.primary_coding_finished_com = False
        self.primary_coding_finished_obj = False
        self.primary_coding_finished_loc = False
        self.primary_coding_finished_emo = False
        self.ready_for_rel_com = False
        self.ready_for_rel_obj = False
        self.ready_for_rel_loc = False
        self.ready_for_rel_emo = False
        self.ready_for_rel_tra = False
        self.rel_coding_finished_com = False
        self.rel_coding_finished_obj = False
        self.rel_coding_finished_loc = False
        self.rel_coding_finished_emo = False
        self.rel_coding_finished_tra = False
        self.moved_to_silver_com = False
        self.moved_to_silver_tra = False
        self.moved_to_silver_obj = False
        self.moved_to_silver_loc = False
        self.moved_to_silver_emo = False
        self.moved_to_gold_com = False
        self.moved_to_gold_tra = False
        self.moved_to_gold_obj = False
        self.moved_to_gold_loc = False
        self.moved_to_gold_emo = False
        self.in_kobo_forms = False
        self.queued = False
        self.id = "{} - {} - {}".format(self.vol_id, self.site_id, self.subj_number)
        self.name = self.id  # TODO For now, revisit this
        self.play_filename = "PLAY_{}{}_NaturalPlay.mp4".format(
            self.vol_id, self.slot_id
        )
        self.play_id = "PLAY_{}{}".format(self.vol_id, self.slot_id)
        self.qa_filename = "PLAY_{}_{}.opf".format(self.site_id, self.subj_number)
        self.coding_filename_prefix = "PLAY_{}{}".format(self.vol_id, self.slot_id)
        self.display_name = "PLAY_{vol_id}{asset_id}-{site_id}-{subnum}-{testdate}-{language}-R{release}".format(
            vol_id=self.vol_id,
            asset_id=self.slot_id,
            site_id=self.site_id,
            subnum=self.subj_number,
            testdate=self.testdate,
            #  exclusion_status="temp",  # TODO fixme
            release=self.permission,
            language=self.language,
        )

        # Lists because there can be multiple videos per
        # task
        self.natural_play = []
        self.house_walk = []
        self.home_question = []
        self.structured_play = []
        self.consent = []
        self.other = []

        self.video_map = {
            "NaturalPlay": self.natural_play,
            "StructuredPlay": self.structured_play,
            "HouseWalkthrough": self.house_walk,
            "Questionnaires": self.home_question,
            "Consent": self.consent,
            "Other": self.other,
        }

    def check_for_form(self, forms):
        for form in forms:
            d = forms[form].get_submissions()
            for sub in d:
                sub = sub.as_dict()
                site_id = sub["site_id"]
                s_num = sub["subject_number"]
                if self.site_id == site_id and self.subj_number == s_num:
                    self.in_kobo_forms = True
                    self.kobo_data = sub
                    return True
        return False

    def is_finished(self):
        flag_sum = sum(
            [
                self.moved_to_gold_tra,
                self.moved_to_gold_emo,
                self.moved_to_gold_loc,
                self.moved_to_gold_obj,
                self.moved_to_gold_com,
                self.moved_to_silver_emo,
                self.moved_to_silver_obj,
                self.moved_to_silver_loc,
                self.moved_to_silver_tra,
                self.moved_to_silver_com,
            ]
        )
        if self.moved_to_gold_tra and flag_sum == 5:
            return True
        elif self.moved_to_silver_tra and flag_sum == 4:
            return True
        else:
            return False

    def is_all_gold(self):
        if all(
            [
                self.moved_to_gold_tra,
                self.moved_to_gold_com,
                self.moved_to_gold_obj,
                self.moved_to_gold_loc,
                self.moved_to_gold_emo,
            ]
        ):
            return True
        else:
            return False

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
        try:
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
        except IndexError:
            self.video_map["Other"].append(asset)

    def print_status(self):
        passes = ["obj", "com", "tra", "loc", "emo"]
        search_results = [[], []]
        search_results[0].append(self.ready_for_qa)
        search_results[0].append(self.ready_for_coding)
        i = 0
        for p in passes:
            search_results[1].append((i, p))
            i += 1
            for status in [
                "assigned_coding_site_{}",
                "primary_coding_finished_{}",
                "ready_for_rel_{}",
                "rel_coding_finished_{}",
                "moved_to_silver_{}",
                "moved_to_gold_{}",
            ]:
                search_results[1].append((i, getattr(self, status.format(p))))
                i += 1
        return search_results


class Lab:
    def __init__(self, site_code, lab_code, pi_fullname, email, institution):
        self.site_code = site_code
        self.lab_code = lab_code
        self.pi_fullname = pi_fullname
        self.email = email
        self.db_volume = "PLAYProject_" + site_code
        self.institution = institution
        self.vol_id = None
        self.code_obj = False
        self.code_loc = False
        self.code_emo = False
        self.code_com = False
        self.code_tra = False
        self.coders = []
        self.assigned_videos = []

    def __str__(self):
        return "{}".format(self.lab_code)


class Site:
    def __init__(self, site_code):
        self.site_code = site_code
        self.db_volume = "PLAYProject_" + site_code
        self.submissions = {}
        self.labs = {}

    def add_video(self, site_id, asset):
        filename = asset["filename"]
        try:
            subj_number = filename.split("_")[2]
        except IndexError:
            subj_number = asset["id"]
        if "-" in subj_number:
            subj_number = subj_number.split("-")[0]
        if subj_number.startswith("S"):
            subj_number = subj_number[1:]
        if asset["id"] not in [s.asset_id for s in self.submissions.values()]:
            if subj_number not in self.submissions:
                self.submissions[subj_number] = Submission(site_id, subj_number, asset)
            self.submissions[subj_number].add_video(asset)

    def get_vol_id(self, databrary_instance):
        self.vol_id = databrary_instance.get_volume_by_name(self.db_volume)


class Datastore:
    VERSION = 2

    def __init__(self):
        self.labs = {}  # lab_code -> lab
        self.sites = {}  # site_code -> site
        self.tra_names = []  # Translator names

        self.statuses = [
            "Connecting to Box, Google, Databrary, and Kobo...",
            "Downloading files from Kobo...",
            "Getting data from Google Sheets...",
            "Getting data from Databrary...",
            "Checking for changes to coded videos...",
            "Checking that permissions are correct...",
            "Performing first-time sync to Box's current state (you might want to get a cup of coffee)...",
            "Finished!",
        ]

        self.error_status = "Error! Please report: {}"

        self.curr_status = 0
        self.synced = False
        self.error_flag = False

    def set_error_state(self, e):
        self.error_status = self.error_status.format(e)
        self.error_flag = True

    def increment_status(self):
        print("INCREMENTING", self.curr_status)
        self.curr_status += 1

    def get_status(self):
        if self.error_flag:
            return self.error_status
        return self.statuses[self.curr_status]

    def add_video(self, asset):
        try:
            site_id = asset["filename"].split("_")[1].strip()
        except IndexError:
            site_id = "TEST" if asset["vol_id"] == "135" else "TEST2"
        try:
            self.sites[site_id].add_video(site_id, asset)
        except KeyError:
            print("ERROR: Could not find video", site_id, asset)
            pass  # If the key isnt found just ignore it for now

    def save(self):
        with open(constants.SAVE_FILE_NAME, "wb") as handle:
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

    def find_submission_by_name(self, coding_prefix):
        print(coding_prefix)
        coding_number = coding_prefix.split("_")[1]
        for s in self.get_submissions():
            print(s.coding_filename_prefix.split("_")[1], coding_number)
            if str(s.coding_filename_prefix.split("_")[1]) == str(coding_number):
                return s
        return None

    def find_submission_fuzzy(self, name):
        if "PLAY_" in name:
            coding_number = name.split("_")[1]
        elif "_" in name:
            coding_number = name.split("_")[0]
        else:
            coding_number = name
        for s in self.get_submissions():
            if str(s.coding_filename_prefix.split("_")[1]) == str(coding_number):
                return s.print_status()
        return "<p>Not found: {}</p>".format(name)

    def find_submission_by_site_subj(self, site, subj):
        print("Finding", site, subj, self.sites[site].submissions)
        return self.sites[site].submissions[subj]

    def find_lab(self, lab_id):
        return self.labs[lab_id]
