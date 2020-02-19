class Submission:
    def __init__(self, kobo_data):
        self.kobo_data = kobo_data
        self.ready_for_qa = False
        self.ready_for_coding = False
        self.moved_to_silver = False
        self.assigned_coding_site = None
        self.primary_coding_finished = False
        self.rel_coding_finished = False
        self.moved_to_gold = False

    def video_exists(self):
        # Check to see if the video is on DB
        pass

    def _to_csv(self):
        # Return a CSV string rep
        pass

class Lab:
    def __init__(self, site_code, lab_code, pi_fullname, email):
        self.site_code = site_code
        self.lab_code = lab_code
        self.pi_fullname = pi_fullname
        self.email = email
        self.db_volume = "PLAYProject_" + site_code
