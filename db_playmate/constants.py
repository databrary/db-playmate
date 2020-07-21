import appdirs
import os

APP_NAME = "db-playmate"
APP_AUTHOR = "Databrary"

PLAY_PREFIX = "PLAY-Project@/"  # For if there is a shared folder

QA_CODING_DIR = PLAY_PREFIX + "automation_doNotTouch/2_PLAY_qa_opfs/1_PLAY_qa_templates"
QA_CODED_DIR = (
    PLAY_PREFIX + "automation_doNotTouch/2_PLAY_qa_opfs/2_PLAY_qa_complete/PLAY_QA_{}"
)
PRI_CODING_DIR = (
    PLAY_PREFIX
    + "automation_doNotTouch/4a_PLAY_coding_opf_templates_and_submissions/PLAY_opfs_{}/PLAY_opfs_{}/1_ToBeCoded_DownloadOnly"
)  # type / lab / 3_Submitted_CannotEditAnymore
PRI_CODED_DIR = (
    PLAY_PREFIX
    + "automation_doNotTouch/4a_PLAY_coding_opf_templates_and_submissions/PLAY_opfs_{}/PLAY_opfs_{}/3_Submitted_CannotEditAnymore"
)  # type / lab / 3_Submitted_CannotEditAnymore
PRI_WORK_DIR = (
    PLAY_PREFIX
    + "automation_doNotTouch/4a_PLAY_coding_opf_templates_and_submissions/PLAY_opfs_{}/PLAY_opfs_{}/2_InProgress"
)  # type / lab / 3_Submitted_CannotEditAnymore

VIDEO_DIR = PLAY_PREFIX + "automation_doNotTouch/1_PLAY_videos_for_coding"


REL_CODING_DIR = (
    PLAY_PREFIX
    + "automation_doNotTouch/5_PLAY_opf_readyforrel/PLAY_rel_{}/{}/1_ToBeCoded_DownloadOnly"
)
REL_CODED_DIR = (
    PLAY_PREFIX
    + "automation_doNotTouch/5_PLAY_opf_readyforrel/PLAY_rel_{}/{}/3_Submitted_CannotEditAnymore"
)
DEFAULT_SAVE_DIR = "env/db_playmate.pickle"

USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
TMP_DATA_DIR = appdirs.user_cache_dir(APP_NAME, APP_AUTHOR)
SAVE_FILE_NAME = USER_DATA_DIR + "/" + "db_playmate.pickle"
GOLD_FINAL_DIR = PLAY_PREFIX + "automation_doNotTouch/7_PLAY_GOLD/{}/"  # Site
SILVER_FINAL_DIR = (
    PLAY_PREFIX + "automation_doNotTouch/8_PLAY_SILVER/{}/{}/"
)  # Site / Pass
os.makedirs(USER_DATA_DIR, exist_ok=True)
os.makedirs(TMP_DATA_DIR, exist_ok=True)
