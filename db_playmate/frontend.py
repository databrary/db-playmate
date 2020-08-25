import os
import pickle
import threading
import time
import sys
import traceback
import requests
import jinja2
import multiprocessing

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngine import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow

from flask import Flask, Response, render_template
from flask_wtf import FlaskForm
from wtforms.fields import SelectField, SelectMultipleField, SubmitField

from db_playmate.bridge import Bridge
from db_playmate.data_model import Datastore, Site
from db_playmate.datavyu import DatavyuTemplateFactory
from db_playmate.process_queue import Job, Queue
from db_playmate.sheets import read_master

from db_playmate.datavyu import DatavyuTemplateFactory as Datavyu

import db_playmate.constants as constants

from db_playmate.configure import config


CONFIG_FILE = constants.USER_DATA_DIR + "/config.toml"
print(CONFIG_FILE, os.path.exists(CONFIG_FILE))


VIDEO_BOX_FOLDER = "PLAY-Project@/automation_doNotTouch/1_PLAY_videos_for_coding"
QA_BOX_FOLDER = "PLAY-Project@/automation_doNotTouch/2_PLAY_qa_opfs/1_PLAY_qa_templates"

app = Flask(__name__)
app.config["SECRET_KEY"] = "you-will-never-guess"
app.register_blueprint(config, url_prefix="/config")

DATASTORE = Datastore()

BRIDGE = 0


class QWebEngineViewWindow(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.page().createStandardContextMenu()

    def closeEvent(self, event):
        print("Close event fired")
        from flask import request

        global DATASTORE
        DATASTORE.box.remove_lockfile()

        func = request.environ.get("werkzeug.server.shutdown")
        try:
            func()
        except:
            pass
        quit()


#  os.environ["QTWEBENGINEPROCESS_PATH"] = "./"
qt_app = QApplication(sys.argv)
WEB = QWebEngineViewWindow()
WEB.setWindowTitle("DB Playmate")

QUEUE = Queue()


class InDbForm(FlaskForm):
    in_databrary = SelectField("In Databrary")
    submit_send_to_qa = SubmitField("Move to Ready for QA")
    submit_remove = SubmitField("Remove from workflow")


class QAForm(FlaskForm):
    ready_for_qa = SelectField("Ready For QA")
    submit_send_to_coding = SubmitField("Send to Coding")
    submit_send_to_silver = SubmitField("Send to Silver")


class CodingForm(FlaskForm):
    ready_for_coding = SelectField("Ready for Coding")
    lab_list = SelectField("List of Labs")
    submit_send_to_lab = SubmitField("Send to Selected Lab")


class TraCodingForm(FlaskForm):
    ready_for_coding = SelectField("Ready for Tra")
    lab_list = SelectField("List of Transcribers")
    being_coded = SelectField("List of Videos being Transcribed")
    submit_send_to_lab = SubmitField("Send to Selected Transcriber")
    submit_send_to_silver = SubmitField("Send to SILVER")
    submit_send_to_gold = SubmitField("Send to GOLD/COM")


class VideosCodedForm(FlaskForm):
    videos_coded = SelectField("Coded Videos")
    videos_not_coded = SelectField("Video Being Coded")
    submit_send_to_rel = SubmitField("Send to Rel")
    submit_send_to_silver = SubmitField("Send to SILVER")
    submit_send_to_gold = SubmitField("Send to GOLD/COM")


class RelForm(FlaskForm):
    ready_for_rel = SelectField("Ready for Rel")
    submit_send_to_gold = SubmitField("Mark Pass as GOLD")
    submit_send_to_silver = SubmitField("Mark Pass as SILVER")
    gold = SelectField("In GOLD")
    silver = SelectField("In Silver")


class QueueForm(FlaskForm):
    actions = SelectMultipleField("Queued Actions")
    results = SelectMultipleField("Results")
    submit_queue = SubmitField("Submit Queue", id="submit_queue")
    remove_item_queue = SubmitField("Remove Selected Action")
    cancel_queue = SubmitField("Cancel Queue")


class RefreshButton(FlaskForm):
    refresh_button = SubmitField("Refresh Videos from Box")


class InSilver(FlaskForm):
    in_silver = SelectField("In Silver")


class InGold(FlaskForm):
    in_gold = SelectField("In Gold")


def create_forms():
    global DATASTORE
    DATASTORE.save()
    labs = DATASTORE.labs.values()
    in_db_form = InDbForm({"width": "200px"})
    in_db = [
        (x.id, x.display_name)
        if not x.in_kobo_forms
        else (x.id, x.display_name + " (in Kobo)")
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.ready_for_qa is False
    ]
    in_db_form.in_databrary.choices = in_db if len(in_db) > 0 else [("-", "-")]

    qa_form = QAForm()
    qa = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.ready_for_qa is True and x.ready_for_coding is False
    ]
    qa_form.ready_for_qa.choices = qa if len(qa) > 0 else [("-", "-")]

    trans_coding_form = TraCodingForm()
    trans_coding_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_tra is None
    ]
    trans_coding_form.ready_for_coding.choices = trans_coding_videos
    lab_list = sorted([(x, x) for x in DATASTORE.tra_names])
    trans_coding_form.lab_list.choices = lab_list

    comm_coding_form = CodingForm()
    comm_coding_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_com is None
        and x.primary_coding_finished_tra
    ]
    comm_coding_form.ready_for_coding.choices = comm_coding_videos
    lab_list = sorted([(x.lab_code, x.lab_code) for x in labs if x.code_com])
    comm_coding_form.lab_list.choices = lab_list

    loc_coding_form = CodingForm()
    loc_coding_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_loc is None
    ]
    loc_coding_form.ready_for_coding.choices = loc_coding_videos
    lab_list = sorted([(x.lab_code, x.lab_code) for x in labs if x.code_loc])
    loc_coding_form.lab_list.choices = lab_list

    obj_coding_form = CodingForm()
    obj_coding_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_obj is None
    ]
    obj_coding_form.ready_for_coding.choices = obj_coding_videos
    lab_list = sorted([(x.lab_code, x.lab_code) for x in labs if x.code_obj])
    obj_coding_form.lab_list.choices = lab_list

    emo_coding_form = CodingForm()
    emo_coding_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_emo is None
    ]
    emo_coding_form.ready_for_coding.choices = emo_coding_videos
    lab_list = sorted([(x.lab_code, x.lab_code) for x in labs if x.code_emo])
    emo_coding_form.lab_list.choices = lab_list

    trans_video_coding_form = VideosCodedForm()
    v_coding_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and ((x.primary_coding_finished_tra and x.ready_for_rel_tra is False))
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and (
            (
                x.primary_coding_finished_tra is False
                and x.assigned_coding_site_tra is not None
            )
        )
    ]
    trans_video_coding_form.videos_coded.choices = v_coding_done
    trans_video_coding_form.videos_not_coded.choices = v_coding_not_done

    loc_video_coding_form = VideosCodedForm()
    v_coding_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_loc
        and x.ready_for_rel_loc is False
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_loc is False
        and x.assigned_coding_site_loc is not None
    ]
    loc_video_coding_form.videos_coded.choices = v_coding_done
    loc_video_coding_form.videos_not_coded.choices = v_coding_not_done

    comm_video_coding_form = VideosCodedForm()
    v_coding_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_com
        and x.ready_for_rel_com is False
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_com is False
        and x.assigned_coding_site_com is not None
        and x.moved_to_gold_tra
    ]
    comm_video_coding_form.videos_coded.choices = v_coding_done
    comm_video_coding_form.videos_not_coded.choices = v_coding_not_done

    emo_video_coding_form = VideosCodedForm()
    v_coding_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_emo
        and x.ready_for_rel_emo is False
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_emo is False
        and x.assigned_coding_site_emo is not None
    ]
    emo_video_coding_form.videos_coded.choices = v_coding_done
    emo_video_coding_form.videos_not_coded.choices = v_coding_not_done

    obj_video_coding_form = VideosCodedForm()
    v_coding_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_obj
        and x.ready_for_rel_obj is False
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_obj is False
        and x.assigned_coding_site_obj is not None
    ]
    obj_video_coding_form.videos_coded.choices = v_coding_done
    obj_video_coding_form.videos_not_coded.choices = v_coding_not_done

    loc_rel_form = RelForm()
    ready_for_rel = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_rel_loc
        and x.rel_coding_finished_loc is False
        and not x.moved_to_gold_loc
    ]
    loc_rel_form.ready_for_rel.choices = ready_for_rel
    gold_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.moved_to_gold_loc
    ]
    loc_rel_form.gold.choices = gold_videos

    emo_rel_form = RelForm()
    ready_for_rel = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_rel_emo
        and x.rel_coding_finished_emo is False
        and not x.moved_to_gold_emo
    ]
    emo_rel_form.ready_for_rel.choices = ready_for_rel
    gold_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.moved_to_gold_emo
    ]
    emo_rel_form.gold.choices = gold_videos

    trans_rel_video_coding_form = RelForm()
    ready_for_rel = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_tra
        and x.ready_for_rel_tra
        and x.rel_coding_finished_tra is False
    ]
    gold_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.moved_to_gold_tra
    ]
    trans_rel_video_coding_form.ready_for_rel.choices = ready_for_rel
    trans_rel_video_coding_form.gold.choices = gold_videos

    comm_rel_form = RelForm()
    ready_for_rel = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_rel_com
        and x.rel_coding_finished_com is False
        and not x.moved_to_gold_com
    ]
    comm_rel_form.ready_for_rel.choices = ready_for_rel
    gold_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.moved_to_gold_com
    ]
    comm_rel_form.gold.choices = gold_videos

    obj_rel_form = RelForm()
    ready_for_rel = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_rel_obj
        and x.rel_coding_finished_com is False
        and not x.moved_to_gold_obj
    ]
    obj_rel_form.ready_for_rel.choices = ready_for_rel
    gold_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if x.moved_to_gold_obj
    ]
    obj_rel_form.gold.choices = gold_videos

    queue_form = QueueForm()
    if len(QUEUE.queued_jobs) > 0:
        queue_items = [(q.display_name, q.display_name) for q in QUEUE.queued_jobs]
    else:
        queue_items = [(" " * 15, " " * 15)]
    queue_form.actions.choices = queue_items
    if len(QUEUE.results) > 0:
        queue_form.results.choices = [(x, x) for x in QUEUE.results]
    else:
        queue_form.results.choices = [(" " * 15, " " * 15)]

    refresh_form = RefreshButton()

    in_silver = InSilver()
    silver_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if any(
            [
                x.moved_to_silver_obj,
                x.moved_to_silver_emo,
                x.moved_to_silver_tra,
                x.moved_to_silver_com,
                x.moved_to_silver_loc,
            ]
        )
        and (x.moved_to_silver_obj or x.moved_to_gold_obj)
        and (x.moved_to_silver_loc or x.moved_to_gold_loc)
        and (x.moved_to_silver_tra or x.moved_to_gold_tra)
        and (x.moved_to_silver_com or x.moved_to_gold_com)
        and (x.moved_to_silver_emo or x.moved_to_gold_emo)
    ]
    in_silver.in_silver.choices = silver_videos

    in_gold = InGold()
    gold_videos = [
        (x.id, x.display_name)
        for site in DATASTORE.sites.values()
        for x in site.submissions.values()
        if all(
            [
                x.moved_to_gold_obj,
                x.moved_to_gold_emo,
                x.moved_to_gold_tra,
                x.moved_to_gold_com,
                x.moved_to_gold_loc,
            ]
        )
    ]
    in_gold.in_gold.choices = gold_videos

    forms = {
        "in_db_form": in_db_form,
        "qa_form": qa_form,
        "trans_coding_form": trans_coding_form,
        "comm_coding_form": comm_coding_form,
        "loc_coding_form": loc_coding_form,
        "obj_coding_form": obj_coding_form,
        "emo_coding_form": emo_coding_form,
        "trans_video_coding_form": trans_video_coding_form,
        "emo_video_coding_form": emo_video_coding_form,
        "obj_video_coding_form": obj_video_coding_form,
        "loc_video_coding_form": loc_video_coding_form,
        "comm_video_coding_form": comm_video_coding_form,
        "obj_rel_form": obj_rel_form,
        "loc_rel_form": loc_rel_form,
        "emo_rel_form": emo_rel_form,
        "comm_rel_form": comm_rel_form,
        "tra_rel_form": trans_rel_video_coding_form,
        "queue_form": queue_form,
        "refresh_button": refresh_form,
        "in_silver": in_silver,
        "in_gold": in_gold,
    }

    DATASTORE.save()
    print("Forms generated!")
    return forms


def initialize():
    global DATASTORE
    global QUEUE
    global BRIDGE
    global CONFIG_FILE

    try:
        BRIDGE = Bridge(CONFIG_FILE)

        if os.path.exists(constants.SAVE_FILE_NAME):
            with open(constants.SAVE_FILE_NAME, "rb") as handle:
                DATASTORE = pickle.load(handle)
        DATASTORE.curr_status = 0
        DATASTORE.increment_status()

        #  BRIDGE.box.check_lockfile()

        # Load the data if it exists, otherwise populate from
        # online resources
        get_kobo_forms(BRIDGE)
        DATASTORE.increment_status()
        sites, labs, tra_names = get_labs(BRIDGE)
        for s in sites:
            if s not in DATASTORE.sites:
                DATASTORE.sites[s] = sites[s]
        for l in labs:
            if l not in DATASTORE.labs:
                DATASTORE.labs[l] = labs[l]
        for t in tra_names:
            if t not in DATASTORE.tra_names:
                DATASTORE.tra_names.append(t)
        DATASTORE.increment_status()
        get_submissions(DATASTORE.sites, BRIDGE, DATASTORE)
        DATASTORE.increment_status()

        # Create a server to show the data
        print("Checking for changes to coded videos...")
        BRIDGE.box.update_coded_videos(DATASTORE)
        DATASTORE.increment_status()

        print("Checking permissions and fixing if needed...")
        BRIDGE.box.update_permissions(DATASTORE)
        DATASTORE.increment_status()

        print("Syncing datastore to Box")
        if not DATASTORE.synced:
            BRIDGE.box.sync_datastore_to_box(DATASTORE)
            DATASTORE.synced = True
        DATASTORE.increment_status()

        DATASTORE.save()
        if DATASTORE.get_status() != "Finished!":
            DATASTORE.increment_status()
    except Exception as e:
        print(traceback.format_exc())
        DATASTORE.set_error_state(traceback.format_exc().replace("\n", " "))
    print("FINISHED")


@app.route("/")
@app.route("/index.html", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def populate_main_page():
    global QUEUE
    print("Generating forms")
    forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_qa", methods=["GET", "POST"])
def send_to_qa():
    global DATASTORE
    global BRIDGE
    in_db_form = InDbForm()
    submitted_data = DATASTORE.find_submission(in_db_form.in_databrary.data)

    def fn(x, box_path, qa_folder):
        x.ready_for_qa = True
        BRIDGE.transfer_databrary_to_box(x, box_path)
        qa_filename = DatavyuTemplateFactory.generate_qa_file(x)
        BRIDGE.transfer_file_to_box(qa_filename, qa_folder)

    QUEUE.add(
        Job(
            target=fn,
            name="SEND TO QA: {}".format(submitted_data.qa_filename),
            args=[submitted_data, VIDEO_BOX_FOLDER, QA_BOX_FOLDER],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/refresh_page", methods=["GET", "POST"])
def refresh_page():
    global BRIDGE
    try:
        BRIDGE.box.update_coded_videos(DATASTORE)
        forms = create_forms()
        return render_template("index.html", forms=forms, queue=QUEUE)
    except:
        pass


@app.route("/send_to_coding", methods=["GET", "POST"])
def send_to_coding():
    global DATASTORE
    global QUEUE
    try:
        qa_form = QAForm()
        submitted_data = DATASTORE.find_submission(qa_form.ready_for_qa.data)

        def fn(x):
            x.ready_for_coding = True

        QUEUE.add(
            Job(
                target=fn,
                name="SEND TO CODING: {}".format(submitted_data.qa_filename),
                args=[submitted_data],
                item=submitted_data,
            )
        )

    except:
        pass

    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_lab_obj", methods=["GET", "POST"])
def send_to_lab_obj():
    global DATASTORE
    global BRIDGE
    global QUEUE
    try:
        coding_form = CodingForm()
        submitted_data = DATASTORE.find_submission(coding_form.ready_for_coding.data)
        lab = DATASTORE.find_lab(coding_form.lab_list.data)

        def fn(x, lab):
            # Download the coded QA file:

            print(constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename)
            qa_file = BRIDGE.box.get_file(
                constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename
            )

            if not qa_file:
                raise Exception("No completed QA file")

            BRIDGE.box.download_file(qa_file, constants.TMP_DATA_DIR)
            output_file = DatavyuTemplateFactory.generate_obj_file(
                x, constants.TMP_DATA_DIR + "/" + x.qa_filename
            )
            print(
                "Uploading {} to {}".format(
                    output_file, constants.PRI_CODING_DIR.format("obj", lab)
                )
            )
            BRIDGE.transfer_file_to_box(
                output_file, constants.PRI_CODING_DIR.format("obj", lab), makedirs=True
            )
            BRIDGE.box.create_folders(constants.PRI_CODED_DIR.format("obj", lab))
            x.assigned_coding_site_obj = lab
            lab.assigned_videos.append(x)

        QUEUE.add(
            Job(
                target=fn,
                name="ASSIGN OBJ LAB: {} -> {}".format(submitted_data.qa_filename, lab),
                args=[submitted_data, lab],
                item=submitted_data,
            )
        )

    except:
        print(traceback.format_exc())

    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_lab_loc", methods=["GET", "POST"])
def send_to_lab_loc():
    global DATASTORE
    global BRIDGE
    global QUEUE
    try:
        coding_form = CodingForm()
        submitted_data = DATASTORE.find_submission(coding_form.ready_for_coding.data)
        lab = DATASTORE.find_lab(coding_form.lab_list.data)

        def fn(x, lab):
            # Download the coded QA file:

            print(constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename)
            qa_file = BRIDGE.box.get_file(
                constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename
            )

            if not qa_file:
                raise Exception("No completed QA file")
            BRIDGE.box.download_file(qa_file, constants.TMP_DATA_DIR)
            output_file = DatavyuTemplateFactory.generate_loc_file(
                x, constants.TMP_DATA_DIR + "/" + x.qa_filename
            )
            print(
                "Uploading {} to {}".format(
                    output_file, constants.PRI_CODING_DIR.format("loc", lab)
                )
            )
            BRIDGE.transfer_file_to_box(
                output_file, constants.PRI_CODING_DIR.format("loc", lab), makedirs=True
            )
            x.assigned_coding_site_loc = lab
            lab.assigned_videos.append(x)
            BRIDGE.box.create_folders(constants.PRI_CODED_DIR.format("loc", lab))

        QUEUE.add(
            Job(
                target=fn,
                name="ASSIGN LOC LAB: {} -> {}".format(submitted_data.qa_filename, lab),
                args=[submitted_data, lab],
                item=submitted_data,
            )
        )

    except:
        print(traceback.format_exc())

    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_lab_emo", methods=["GET", "POST"])
def send_to_lab_emo():
    global DATASTORE
    global BRIDGE
    global QUEUE
    try:
        coding_form = CodingForm()
        submitted_data = DATASTORE.find_submission(coding_form.ready_for_coding.data)
        lab = DATASTORE.find_lab(coding_form.lab_list.data)

        def fn(x, lab):
            # Download the coded QA file:

            print(constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename)
            qa_file = BRIDGE.box.get_file(
                constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename
            )

            if not qa_file:
                raise Exception("No completed QA file")

            BRIDGE.box.download_file(qa_file, constants.TMP_DATA_DIR)
            output_file = DatavyuTemplateFactory.generate_emo_file(
                x, constants.TMP_DATA_DIR + "/" + x.qa_filename
            )
            print(
                "Uploading {} to {}".format(
                    output_file, constants.PRI_CODING_DIR.format("emo", lab)
                )
            )
            BRIDGE.transfer_file_to_box(
                output_file, constants.PRI_CODING_DIR.format("emo", lab), makedirs=True
            )
            BRIDGE.box.create_folders(constants.PRI_CODED_DIR.format("emo", lab))
            x.assigned_coding_site_emo = lab
            lab.assigned_videos.append(x)

        QUEUE.add(
            Job(
                target=fn,
                name="ASSIGN EMO LAB: {} -> {}".format(submitted_data.qa_filename, lab),
                args=[submitted_data, lab],
                item=submitted_data,
            )
        )

    except:
        print(traceback.format_exc())

    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_lab_tra", methods=["GET", "POST"])
def send_to_lab_tra():
    global DATASTORE
    global QUEUE
    global BRIDGE
    try:
        coding_form = TraCodingForm()
        submitted_data = DATASTORE.find_submission(coding_form.ready_for_coding.data)
        lab = coding_form.lab_list.data

        def fn(x, lab):
            # Download the coded QA file:

            print(constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename)
            qa_file = BRIDGE.box.get_file(
                constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename
            )
            if not qa_file:
                raise Exception("No completed QA file")

            BRIDGE.box.download_file(qa_file, constants.TMP_DATA_DIR)
            output_file = DatavyuTemplateFactory.generate_tra_file(
                x, constants.TMP_DATA_DIR + "/" + x.qa_filename
            )
            print(
                "Uploading {} to {}".format(
                    output_file, constants.PRI_CODING_DIR.format("tra", lab)
                )
            )
            BRIDGE.transfer_file_to_box(
                output_file, constants.PRI_CODING_DIR.format("tra", lab), makedirs=True
            )
            BRIDGE.box.create_folders(constants.PRI_CODED_DIR.format("tra", lab))
            x.assigned_coding_site_tra = lab
            lab.assigned_videos.append(x)

        QUEUE.add(
            Job(
                target=fn,
                name="ASSIGN TRA LAB: {} -> {}".format(submitted_data.qa_filename, lab),
                args=[submitted_data, lab],
                item=submitted_data,
            )
        )

    except:
        print(traceback.format_exc())

    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_lab_comm", methods=["GET", "POST"])
def send_to_lab_comm():
    global DATASTORE
    global QUEUE
    global BRIDGE
    try:
        coding_form = CodingForm()
        submitted_data = DATASTORE.find_submission(coding_form.ready_for_coding.data)
        lab = DATASTORE.find_lab(coding_form.lab_list.data)

        def fn(x, lab):
            # Download the coded QA file:

            qa_file = BRIDGE.box.get_file(
                constants.PRI_CODED_DIR.format("tra", x.assigned_coding_site_tra)
                + "/"
                + x.coding_filename_prefix
                + "_tra.opf"
            )
            if not qa_file:
                raise Exception("No completed Tra file")

            BRIDGE.box.download_file(qa_file, constants.TMP_DATA_DIR)
            output_file = DatavyuTemplateFactory.generate_com_file(
                x, constants.TMP_DATA_DIR + "/" + x.qa_filename
            )
            print(
                "Uploading {} to {}".format(
                    output_file, constants.PRI_CODING_DIR.format("com", lab)
                )
            )
            BRIDGE.transfer_file_to_box(
                output_file, constants.PRI_CODING_DIR.format("com", lab), makedirs=True
            )

            BRIDGE.box.create_folders(constants.PRI_CODED_DIR.format("com", lab))
            x.assigned_coding_site_com = lab
            lab.assigned_videos.append(x)
            x.moved_to_gold_tra = True

        QUEUE.add(
            Job(
                target=fn,
                name="ASSIGN COMM LAB: {} -> {}".format(
                    submitted_data.qa_filename, lab
                ),
                args=[submitted_data, lab],
                item=submitted_data,
            )
        )

    except:
        print(traceback.format_exc())

    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_rel_tra", methods=["GET", "POST"])
def send_to_rel_tra():
    global DATASTORE
    global QUEUE
    global BRIDGE
    try:
        video_coding_form = VideosCodedForm()
        submitted_data = DATASTORE.find_submission(video_coding_form.videos_coded.data)

        def fn(x):
            site = x.assigned_coding_site_tra
            BRIDGE.box.download_file(
                "/".join(
                    [
                        constants.PRI_CODED_DIR.format("tra", site),
                        x.coding_filename_prefix + "_tra.opf",
                    ]
                ),
                constants.TMP_DATA_DIR,
            )
            f = Datavyu.generate_rel_file(x, "tra")
            BRIDGE.box.upload_file(
                f,
                constants.REL_CODING_DIR.format(
                    "tra", submitted_data.assigned_coding_site_loc
                ),
            )
            x.ready_for_rel_tra = True

        QUEUE.add(
            Job(
                target=fn,
                name="READY FOR TRA REL: {}".format(submitted_data.qa_filename),
                args=[submitted_data],
                item=submitted_data,
            )
        )

    except:
        pass

    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_rel_obj", methods=["GET", "POST"])
def send_to_rel_obj():
    global DATASTORE
    global QUEUE
    global BRIDGE
    try:
        video_coding_form = VideosCodedForm()
        submitted_data = DATASTORE.find_submission(video_coding_form.videos_coded.data)

        def fn(x):
            site = x.assigned_coding_site_obj
            BRIDGE.box.download_file(
                "/".join(
                    [
                        constants.PRI_CODED_DIR.format("obj", site),
                        x.coding_filename_prefix + "_obj.opf",
                    ]
                ),
                constants.TMP_DATA_DIR,
            )
            f = Datavyu.generate_rel_file(x, "obj")
            BRIDGE.box.upload_file(
                f,
                constants.REL_CODING_DIR.format(
                    "obj", submitted_data.assigned_coding_site_loc
                ),
            )
            x.ready_for_rel_obj = True

        QUEUE.add(
            Job(
                target=fn,
                name="READY FOR OBJ REL: {}".format(submitted_data.qa_filename),
                args=[submitted_data],
                item=submitted_data,
            )
        )

    except:
        print(traceback.format_exc())

    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_rel_loc", methods=["GET", "POST"])
def send_to_rel_loc():
    global DATASTORE
    global QUEUE
    global BRIDGE
    try:
        video_coding_form = VideosCodedForm()
        submitted_data = DATASTORE.find_submission(video_coding_form.videos_coded.data)

        def fn(x):
            site = x.assigned_coding_site_loc
            BRIDGE.box.download_file(
                "/".join(
                    [
                        constants.PRI_CODED_DIR.format("loc", site),
                        x.coding_filename_prefix + "_loc.opf",
                    ]
                ),
                constants.TMP_DATA_DIR,
            )

            f = Datavyu.generate_rel_file(x, "loc")
            BRIDGE.box.upload_file(
                f,
                constants.REL_CODING_DIR.format(
                    "loc", submitted_data.assigned_coding_site_loc
                ),
            )
            x.ready_for_rel_loc = True

        QUEUE.add(
            Job(
                target=fn,
                name="READY FOR LOC REL: {}".format(submitted_data.qa_filename),
                args=[submitted_data],
                item=submitted_data,
            )
        )

    except:
        pass

    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_rel_emo", methods=["GET", "POST"])
def send_to_rel_emo():
    global DATASTORE
    global QUEUE
    global BRIDGE
    try:
        video_coding_form = VideosCodedForm()
        submitted_data = DATASTORE.find_submission(video_coding_form.videos_coded.data)

        def fn(x):
            site = x.assigned_coding_site_emo
            BRIDGE.box.download_file(
                "/".join(
                    [
                        constants.PRI_CODED_DIR.format("emo", site),
                        x.coding_filename_prefix + "_emo.opf",
                    ]
                ),
                constants.TMP_DATA_DIR,
            )

            f = Datavyu.generate_rel_file(x, "emo")
            BRIDGE.box.upload_file(
                f,
                constants.REL_CODING_DIR.format(
                    "emo", submitted_data.assigned_coding_site_emo
                ),
            )
            x.ready_for_rel_emo = True

        QUEUE.add(
            Job(
                target=fn,
                name="READY FOR EMO REL: {}".format(submitted_data.qa_filename),
                args=[submitted_data],
                item=submitted_data,
            )
        )

    except:
        print(traceback.format_exc())
    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_rel_trans", methods=["GET", "POST"])
def send_to_rel_trans():
    global DATASTORE
    global QUEUE
    global BRIDGE
    try:
        video_coding_form = VideosCodedForm()
        submitted_data = DATASTORE.find_submission(video_coding_form.videos_coded.data)

        if video_coding_form.submit_send_to_rel:

            def fn(x):
                site = x.assigned_coding_site_tra
                BRIDGE.box.download_file(
                    "/".join(
                        [
                            constants.PRI_CODED_DIR.format("tra", site),
                            x.coding_filename_prefix + "_tra.opf",
                        ]
                    ),
                    constants.TMP_DATA_DIR,
                )

                f = Datavyu.generate_rel_file(x, "tra")
                BRIDGE.box.upload_file(
                    f,
                    constants.REL_CODING_DIR.format(
                        "tra", submitted_data.assigned_coding_site_tra
                    ),
                )
                x.ready_for_rel_tra = True
                x.moved_to_gold_tra = True  # TODO REMOVE THIS

            QUEUE.add(
                Job(
                    target=fn,
                    name="READY FOR TRA REL: {}".format(submitted_data.qa_filename),
                    args=[submitted_data],
                    item=submitted_data,
                )
            )
        elif video_coding_form.submit_send_to_gold.data:

            def fn(x):
                x.moved_to_gold_tra = True
                QUEUE.add(
                    Job(
                        target=fn,
                        name="READY FOR TRA GOLD/COM: {}".format(
                            submitted_data.qa_filename
                        ),
                        args=[submitted_data],
                        item=submitted_data,
                    )
                )

        elif video_coding_form.submit_send_to_silver.data:

            def fn(x):
                x.moved_to_silver_tra = True
                QUEUE.add(
                    Job(
                        target=fn,
                        name="MARK AS SILVER TRA: {}".format(
                            submitted_data.qa_filename
                        ),
                        args=[submitted_data],
                        item=submitted_data,
                    )
                )

    except:
        print(traceback.format_exc())
    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_rel_comm", methods=["GET", "POST"])
def send_to_rel_comm():
    global DATASTORE
    global BRIDGE
    global QUEUE
    try:
        video_coding_form = VideosCodedForm()
        submitted_data = DATASTORE.find_submission(video_coding_form.videos_coded.data)

        def fn(x):
            site = x.assigned_coding_site_com
            BRIDGE.box.download_file(
                "/".join(
                    [
                        constants.PRI_CODED_DIR.format("com", site),
                        x.coding_filename_prefix + "_com.opf",
                    ]
                ),
                constants.TMP_DATA_DIR,
            )

            f = Datavyu.generate_rel_file(x, "com")
            BRIDGE.box.upload_file(
                f,
                constants.REL_CODING_DIR.format(
                    "tra", submitted_data.assigned_coding_site_tra
                ),
            )
            x.ready_for_rel_com = True

        QUEUE.add(
            Job(
                target=fn,
                name="READY FOR TRA REL: {}".format(submitted_data.qa_filename),
                args=[submitted_data],
                item=submitted_data,
            )
        )

    except:
        print(traceback.format_exc())
    finally:
        forms = create_forms()
    return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/send_to_gold_tra", methods=["GET", "POST"])
def send_to_gold_tra():
    try:
        rel_form = RelForm()
        global DATASTORE
        submitted_data = DATASTORE.find_submission(rel_form.ready_for_rel.data)

        if rel_form.submit_send_to_gold.data:

            def fn(x):
                x.moved_to_gold_tra = True
                process_finished_asset(x)

            name = "MARK AS GOLD TRA: {}".format(submitted_data.qa_filename)
        else:

            def fn(x):
                x.moved_to_silver_tra = True
                process_finished_asset(x)

            name = "MARK AS SILVER TRA: {}".format(submitted_data.qa_filename)

        QUEUE.add(
            Job(target=fn, name=name, args=[submitted_data], item=submitted_data,)
        )

        forms = create_forms()
        return render_template("index.html", forms=forms, queue=QUEUE)
    except:
        print(traceback.format_exc())


@app.route("/send_to_gold_obj", methods=["GET", "POST"])
def send_to_gold_obj():
    try:
        rel_form = RelForm()
        global DATASTORE
        submitted_data = DATASTORE.find_submission(rel_form.ready_for_rel.data)

        if rel_form.submit_send_to_gold.data:

            def fn(x):
                x.moved_to_gold_obj = True
                process_finished_asset(x)

            name = "MARK AS GOLD OBJ: {}".format(submitted_data.qa_filename)
        else:

            def fn(x):
                x.moved_to_silver_obj = True
                process_finished_asset(x)

            name = "MARK AS SILVER OBJ: {}".format(submitted_data.qa_filename)

        QUEUE.add(
            Job(target=fn, name=name, args=[submitted_data], item=submitted_data,)
        )

        forms = create_forms()
        return render_template("index.html", forms=forms, queue=QUEUE)
    except:
        print(traceback.format_exc())


@app.route("/send_to_gold_loc", methods=["GET", "POST"])
def send_to_gold_loc():
    try:
        rel_form = RelForm()
        global DATASTORE
        submitted_data = DATASTORE.find_submission(rel_form.ready_for_rel.data)

        if rel_form.submit_send_to_gold.data:

            def fn(x):
                x.moved_to_gold_loc = True
                process_finished_asset(x)

            name = "MARK AS GOLD LOC: {}".format(submitted_data.qa_filename)
        else:

            def fn(x):
                x.moved_to_silver_loc = True
                process_finished_asset(x)

            name = "MARK AS SILVER LOC: {}".format(submitted_data.qa_filename)

        QUEUE.add(
            Job(target=fn, name=name, args=[submitted_data], item=submitted_data,)
        )

        forms = create_forms()
        return render_template("index.html", forms=forms, queue=QUEUE)
    except:
        print(traceback.format_exc())


@app.route("/send_to_gold_emo", methods=["GET", "POST"])
def send_to_gold_emo():
    try:
        rel_form = RelForm()
        global DATASTORE
        submitted_data = DATASTORE.find_submission(rel_form.ready_for_rel.data)

        if rel_form.submit_send_to_gold.data:

            def fn(x):
                x.moved_to_gold_emo = True
                process_finished_asset(x)

            name = "MARK AS GOLD EMO: {}".format(submitted_data.qa_filename)
        else:

            def fn(x):
                x.moved_to_silver_emo = True
                process_finished_asset(x)

            name = "MARK AS SILVER EMO: {}".format(submitted_data.qa_filename)

        QUEUE.add(
            Job(target=fn, name=name, args=[submitted_data], item=submitted_data,)
        )

        forms = create_forms()
        return render_template("index.html", forms=forms, queue=QUEUE)
    except:
        print(traceback.format_exc())


@app.route("/send_to_gold_comm", methods=["GET", "POST"])
def send_to_gold_comm():
    try:
        rel_form = RelForm()
        global DATASTORE
        submitted_data = DATASTORE.find_submission(rel_form.ready_for_rel.data)

        if rel_form.submit_send_to_gold.data:

            def fn(x):
                x.moved_to_gold_com = True
                process_finished_asset(x)

            name = "MARK AS GOLD COM: {}".format(submitted_data.qa_filename)
        else:

            def fn(x):
                x.moved_to_silver_com = True
                process_finished_asset(x)

            name = "MARK AS SILVER COM: {}".format(submitted_data.qa_filename)

        QUEUE.add(
            Job(target=fn, name=name, args=[submitted_data], item=submitted_data,)
        )

        forms = create_forms()
        return render_template("index.html", forms=forms, queue=QUEUE)
    except:
        print(traceback.format_exc())


def process_finished_asset(asset):
    # Make sure that we are in fact done with this video
    print("All gold?", asset.is_all_gold())
    print("Finished?", asset.is_finished())
    if asset.is_finished():
        print("Detected finished video")
        if asset.is_all_gold():
            print("Video is GOLD!")
            send_to_gold(asset)
        else:
            print("Video is Silver!")
            send_to_silver(asset)


def send_to_gold(asset):
    global BRIDGE
    # Stich OPF
    files = BRIDGE.box.get_finished_opf_files(asset)
    combined_file = Datavyu.combine_files(
        "/".join(
            [constants.TMP_DATA_DIR, asset.coding_filename_prefix + "_combined.opf"]
        ),
        *files
    )
    print("COMBINED FILENAME", combined_file)
    print("DEST", constants.GOLD_FINAL_DIR.format(asset.site_id))
    print(
        "/".join(
            [constants.TMP_DATA_DIR, asset.coding_filename_prefix + "_combined.opf"]
        )
    )
    BRIDGE.box.upload_file(
        combined_file, constants.GOLD_FINAL_DIR.format(asset.site_id), True
    )
    # Mark in DB
    for p in ["tra", "com", "loc", "obj", "emo"]:
        mark_as_gold(asset, p)


def send_to_silver(asset):
    global BRIDGE
    files = BRIDGE.box.get_finished_opf_files(asset)
    for f in files:
        BRIDGE.box.upload_file(
            f, constants.SILVER_FINAL_DIR.format(asset.site_id, asset.subj_number)
        )

    for p in ["tra", "com", "loc", "obj", "emo"]:
        if getattr(asset, "moved_to_gold_" + p):
            mark_as_gold(asset, p)
        else:
            mark_as_silver(asset, p)


def mark_as_gold(asset, coding_pass):
    # Mark the video as GOLD in databrary
    global BRIDGE
    BRIDGE.databrary.write_tag(asset, coding_pass + "_GOLD")


def mark_as_silver(asset, coding_pass):
    global BRIDGE
    BRIDGE.databrary.write_tag(asset, coding_pass + "_SILVER")


@app.route("/queue_action", methods=["GET", "POST"])
def queue_action():
    global QUEUE
    try:
        queue_form = QueueForm()
        if queue_form.submit_queue.data:
            # Execute queue
            QUEUE.run()
            results = []
            for i, job in enumerate(QUEUE.queued_jobs):
                if job.status == 0:
                    results.append((i, " Completed"))
                else:
                    results.append((i, job.error_msg))
            queue_form.results.choices = results

            # queue.clear()
            # Handle any errors that have occurred
        if queue_form.remove_item_queue.data:
            to_remove = queue_form.actions.data
            for i in QUEUE.queued_jobs:
                if i.display_name == to_remove:
                    QUEUE.queued_jobs.remove(i)
                    break
        if queue_form.cancel_queue:
            QUEUE.clear()

        forms = create_forms()
        return render_template("index.html", forms=forms, queue=QUEUE)
    except:
        forms = create_forms()
        return render_template("index.html", forms=forms, queue=QUEUE)


@app.route("/progress")
def progress():
    global QUEUE

    print(QUEUE.status)
    return Response("data:{}\n\n".format(QUEUE.status), mimetype="text/event-stream")


@app.route("/loading")
def loading():
    global DATASTORE
    return render_template("loading.html")


@app.route("/status")
def status():
    global DATASTORE

    print(DATASTORE.get_status())
    return Response(
        "data:{}\n\n".format(DATASTORE.get_status()), mimetype="text/event-stream"
    )


def check_for_new():
    # Check Kobo for a list of new files that need to be sent to QA
    pass


def get_labs(bridge):
    sites, labs, tra_names = read_master()
    for site in sites.values():
        site.get_vol_id(bridge.db)

    return sites, labs, tra_names


def get_submissions(sites, bridge, datastore):
    for site in sites.values():
        if site.vol_id is None:
            continue
        print("Getting submissions for vol_id", site.vol_id)
        assets = bridge.db.get_assets_for_volume(site.vol_id, gold_only=False)
        if assets is not None:
            for a in assets:
                print(a)
                if a["filename"].endswith(".mp4"):
                    try:
                        datastore.add_video(a)
                        print("FOUND VIDEO!", a)
                    except IndexError as e:
                        print("Error adding video")
                        print(e)
    for sub in datastore.get_submissions():
        sub.check_for_form(bridge.kobo.get_forms())


def get_kobo_forms(bridge):
    bridge.transfer_kobo_to_box()


def startup():
    # Set up the Flask server we'll be using

    # Set up the DB/Box/Kobo BRIDGE
    global DATASTORE
    global QUEUE
    global CONFIG_FILE
    global WEB

    if not os.path.exists(CONFIG_FILE):
        url = "http://localhost:5000/config"
    else:
        url = "http://localhost:5000/loading"

    def load_browser(web, url):
        time.sleep(1.25)
        WEB.load(QUrl(url))
        WEB.show()

    # Grab the latest template.html from github for use in index.html
    with open(constants.TMP_DATA_DIR + "/index.html", "w") as handle:
        print("Downloading index.html from Git")
        template_file = requests.get(constants.GIT_TEMPLATE_LINK)
        handle.write(template_file.text)

    my_loader = jinja2.ChoiceLoader(
        [jinja2.FileSystemLoader([constants.TMP_DATA_DIR]), app.jinja_loader]
    )
    app.jinja_loader = my_loader

    init_thread = threading.Thread(target=initialize)
    init_thread.start()
    server = threading.Thread(target=lambda x: x.run(), args=(app,))
    server.start()
    load_browser(WEB, url)

    # This line is critical to avoid a PyQT race condition
    sys.exit(qt_app.exec_())


if __name__ == "__main__":
    startup()
