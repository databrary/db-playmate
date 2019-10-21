class KoboForm:
    """Stores information about a particular form."""

    def __init__(self, json):
        """Parse in information from a JSON formatted string."""
        self.submissions = []
        self.json = json

    def __parse__(self):
        self.num_columns = self.json["row_count"]
        self.id = self.json["uid"]
        self.name = self.json["name"]
        self.type = self.json["asset_type"]
        self.version_id = self.json["version_id"]
        self.num_submissions = self.json["deployment__submission_count"]

    def _add_submission(self, data):
        self.submissions.append(data)
