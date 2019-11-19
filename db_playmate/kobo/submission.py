class Submission:
    """Wrapper for a dictionary mapping questions to answers."""

    def __init__(self, version=None):
        self.answers = {}
        self.version = version
