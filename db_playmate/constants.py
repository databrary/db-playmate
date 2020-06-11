import appdirs
import os

APP_NAME = "DB Playmate"
APP_AUTHOR = "Databrary"

QA_DIR = ""
PLAY_PREFIX = "PLAY-Project@/"  # For if there is a shared folder

QA_CODED_DIR = (
    PLAY_PREFIX + "automation_doNotTouch/2_PLAY_qa_opfs/2_PLAY_qa_complete/PLAY_QA_{}/"
)
PRI_CODING_DIR = (
    PLAY_PREFIX
    + "automation_doNotTouch/4a_PLAY_coding_opf_templates_and_submissions/PLAY_opfs_{}/PLAY_opfs_{}/1_ToBeCoded_DownloadOnly"
)  # type / lab / 3_Submitted_CannotEditAnymore
PRI_CODED_DIR = (
    PLAY_PREFIX
    + "automation_doNotTouch/4a_PLAY_coding_opf_templates_and_submissions/PLAY_opfs_{}/PLAY_opfs_{}/3_Submitted_CannotEditAnymore/"
)  # type / lab / 3_Submitted_CannotEditAnymore
REL_CODED_DIR = (
    PLAY_PREFIX + "automation_doNotTouch/5_PLAY_opf_readyforrel/PLAY_rel_{}/{}/"
)
DEFAULT_SAVE_DIR = "env/db_playmate.pickle"

USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
TMP_DATA_DIR = appdirs.user_cache_dir(APP_NAME, APP_AUTHOR)
os.makedirs(USER_DATA_DIR, exist_ok=True)
os.makedirs(TMP_DATA_DIR, exist_ok=True)
