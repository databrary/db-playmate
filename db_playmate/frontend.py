import os
import pickle
import threading
import webbrowser

from flask import Flask, Response, render_template
from flask_wtf import FlaskForm
from wtforms.fields import SelectField, SelectMultipleField, SubmitField

from db_playmate.bridge import Bridge
from db_playmate.data_model import Datastore
from db_playmate.datavyu import DatavyuTemplateFactory
from db_playmate.process_queue import Job, Queue
from db_playmate.sheets import read_master

import db_playmate.constants as constants

SAVE_FILE = "env/db_playmate.pickle"

VIDEO_BOX_FOLDER = "PLAY-Project@/automation_doNotTouch/1_PLAY_videos_for_coding"
QA_BOX_FOLDER = "PLAY-Project@/automation_doNotTouch/2_PLAY_qa_opfs/1_PLAY_qa_templates"

app = Flask(__name__)
app.config["SECRET_KEY"] = "you-will-never-guess"
global datastore
datastore = Datastore()

global forms
forms = {}

global bridge
global queue
queue = Queue()


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
    lab_list = SelectField("List of Translators")
    submit_send_to_lab = SubmitField("Send to Selected Translator")


class VideosCodedForm(FlaskForm):
    videos_coded = SelectField("Coded Videos")
    videos_not_coded = SelectField("Video Being Coded")
    submit_send_to_rel = SubmitField("Send to Rel")


class RelForm(FlaskForm):
    ready_for_rel = SelectField("Ready for Rel")
    submit_send_to_gold = SubmitField("Send to GOLD")
    gold = SelectField("In GOLD")


class QueueForm(FlaskForm):
    actions = SelectMultipleField("Queued Actions")
    results = SelectMultipleField("Results")
    submit_queue = SubmitField("Submit Queue")
    remove_item_queue = SubmitField("Remove Selected Action")
    cancel_queue = SubmitField("Cancel Queue")


def create_forms():
    global datastore
    in_db_form = InDbForm({"width": "200px"})
    in_db = [
        (x.id, x.display_name)
        if not x.in_kobo_forms
        else (x.id, x.display_name + " (in Kobo)")
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.ready_for_qa is False
    ]
    in_db_form.in_databrary.choices = in_db if len(in_db) > 0 else [("-", "-")]

    qa_form = QAForm()
    qa = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.ready_for_qa is True and x.ready_for_coding is False
    ]
    qa_form.ready_for_qa.choices = qa if len(qa) > 0 else [("-", "-")]

    trans_coding_form = TraCodingForm()
    trans_coding_videos = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_tra is None
    ]
    trans_coding_form.ready_for_coding.choices = trans_coding_videos
    lab_list = [(x, x) for x in datastore.tra_names]
    trans_coding_form.lab_list.choices = lab_list

    comm_coding_form = CodingForm()
    comm_coding_videos = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_com is None
        and x.primary_coding_finished_tra
    ]
    for x in comm_coding_videos:
        print(x.id, x.primary_coding_finished_tra)
    comm_coding_form.ready_for_coding.choices = comm_coding_videos
    lab_list = [(x.lab_code, x.lab_code) for x in datastore.labs if x.code_com]
    comm_coding_form.lab_list.choices = lab_list

    loc_coding_form = CodingForm()
    loc_coding_videos = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_loc is None
    ]
    loc_coding_form.ready_for_coding.choices = loc_coding_videos
    lab_list = [(x.lab_code, x.lab_code) for x in datastore.labs if x.code_loc]
    loc_coding_form.lab_list.choices = lab_list

    obj_coding_form = CodingForm()
    obj_coding_videos = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_obj is None
    ]
    obj_coding_form.ready_for_coding.choices = obj_coding_videos
    lab_list = [(x.lab_code, x.lab_code) for x in datastore.labs if x.code_obj]
    obj_coding_form.lab_list.choices = lab_list

    emo_coding_form = CodingForm()
    emo_coding_videos = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.ready_for_coding is True
        and x.assigned_coding_site_emo is None
    ]
    emo_coding_form.ready_for_coding.choices = emo_coding_videos
    lab_list = [(x.lab_code, x.lab_code) for x in datastore.labs if x.code_emo]
    emo_coding_form.lab_list.choices = lab_list

    trans_video_coding_form = VideosCodedForm()
    v_coding_done = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.primary_coding_finished_tra and x.ready_for_rel is False
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_tra is False
        and x.assigned_coding_site_tra is not None
    ]
    trans_video_coding_form.videos_coded.choices = v_coding_done
    trans_video_coding_form.videos_not_coded.choices = v_coding_not_done

    loc_video_coding_form = VideosCodedForm()
    v_coding_done = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.primary_coding_finished_loc and x.ready_for_rel is False
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
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
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.primary_coding_finished_com and x.ready_for_rel is False
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued
        and x.primary_coding_finished_com is False
        and x.assigned_coding_site_com is not None
    ]
    comm_video_coding_form.videos_coded.choices = v_coding_done
    comm_video_coding_form.videos_not_coded.choices = v_coding_not_done

    emo_video_coding_form = VideosCodedForm()
    v_coding_done = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.primary_coding_finished_emo and x.ready_for_rel is False
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
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
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.primary_coding_finished_obj and x.ready_for_rel is False
    ]
    v_coding_not_done = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
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
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.ready_for_rel_loc and x.rel_coding_finished_loc is False
    ]
    loc_rel_form.ready_for_rel.choices = ready_for_rel
    gold_videos = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.moved_to_gold_loc
    ]
    loc_rel_form.gold.choices = gold_videos

    emo_rel_form = RelForm()
    ready_for_rel = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.ready_for_rel_emo and x.rel_coding_finished_emo is False
    ]
    emo_rel_form.ready_for_rel.choices = ready_for_rel
    gold_videos = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.moved_to_gold_emo
    ]
    emo_rel_form.gold.choices = gold_videos

    comm_rel_form = RelForm()
    ready_for_rel = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.ready_for_rel_com and x.ready_for_rel_com is False
    ]
    comm_rel_form.ready_for_rel.choices = ready_for_rel
    gold_videos = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.moved_to_gold_com
    ]
    comm_rel_form.gold.choices = gold_videos

    obj_rel_form = RelForm()
    ready_for_rel = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.ready_for_rel_obj and x.ready_for_rel_obj is False
    ]
    obj_rel_form.ready_for_rel.choices = ready_for_rel
    gold_videos = [
        (x.id, x.display_name)
        for site in datastore.sites.values()
        for x in site.submissions.values()
        if not x.queued and x.moved_to_gold_obj
    ]
    obj_rel_form.gold.choices = gold_videos

    queue_form = QueueForm()
    if len(queue.queued_jobs) > 0:
        queue_items = [(q.display_name, q.display_name) for q in queue.queued_jobs]
    else:
        queue_items = [(" " * 15, " " * 15)]
    queue_form.actions.choices = queue_items
    if len(queue.results) > 0:
        queue_form.results.choices = [(x, x) for x in queue.results]
    else:
        queue_form.results.choices = [(" " * 15, " " * 15)]

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
        "queue_form": queue_form,
    }

    return forms


@app.route("/")
@app.route("/index.html", methods=["GET", "POST"])
def populate_main_page():
    global forms
    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_qa", methods=["GET", "POST"])
def send_to_qa():
    global datastore
    global bridge
    global forms
    in_db_form = InDbForm()
    print(in_db_form.in_databrary.data, forms["in_db_form"].in_databrary.data)
    submitted_data = datastore.find_submission(in_db_form.in_databrary.data)

    def fn(x, box_path, qa_folder):
        x.ready_for_qa = True
        bridge.transfer_databrary_to_box(x, box_path)
        qa_filename = DatavyuTemplateFactory.generate_qa_file(x)
        bridge.transfer_file_to_box(qa_filename, qa_folder)

    queue.add(
        Job(
            target=fn,
            name="SEND TO QA: {}".format(submitted_data.qa_filename),
            args=[submitted_data, VIDEO_BOX_FOLDER, QA_BOX_FOLDER],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_coding", methods=["GET", "POST"])
def send_to_coding():
    global datastore
    qa_form = QAForm()
    submitted_data = datastore.find_submission(qa_form.ready_for_qa.data)

    def fn(x):
        x.ready_for_coding = True

    queue.add(
        Job(
            target=fn,
            name="SEND TO CODING: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_lab_obj", methods=["GET", "POST"])
def send_to_lab_obj():
    global datastore
    coding_form = CodingForm()
    submitted_data = datastore.find_submission(coding_form.ready_for_coding.data)
    lab = datastore.find_lab(coding_form.lab_list.data)

    def fn(x, lab):
        # Download the coded QA file:

        print(constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename)
        qa_file = bridge.box.get_file(
            constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename
        )

        if not qa_file:
            raise Exception("No completed QA file")

        bridge.box.download_file(qa_file, constants.TMP_DIR)
        output_file = DatavyuTemplateFactory.generate_obj_file(
            x, constants.TMP_DIR + "/" + x.qa_filename
        )
        print(
            "Uploading {} to {}".format(
                output_file, constants.PRI_CODING_DIR.format("obj", lab)
            )
        )
        bridge.transfer_file_to_box(
            output_file, constants.PRI_CODING_DIR.format("obj", lab), makedirs=True
        )
        x.assigned_coding_site_obj = lab

    queue.add(
        Job(
            target=fn,
            name="ASSIGN OBJ LAB: {} -> {}".format(submitted_data.qa_filename, lab),
            args=[submitted_data, lab],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_lab_loc", methods=["GET", "POST"])
def send_to_lab_loc():
    global datastore
    coding_form = CodingForm()
    submitted_data = datastore.find_submission(coding_form.ready_for_coding.data)
    lab = datastore.find_lab(coding_form.lab_list.data)

    def fn(x, lab):
        # Download the coded QA file:

        print(constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename)
        qa_file = bridge.box.get_file(
            constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename
        )

        if not qa_file:
            raise Exception("No completed QA file")
        bridge.box.download_file(qa_file, constants.TMP_DIR)
        output_file = DatavyuTemplateFactory.generate_loc_file(
            x, constants.TMP_DIR + "/" + x.qa_filename
        )
        print(
            "Uploading {} to {}".format(
                output_file, constants.PRI_CODING_DIR.format("loc", lab)
            )
        )
        bridge.transfer_file_to_box(
            output_file, constants.PRI_CODING_DIR.format("loc", lab), makedirs=True
        )
        x.assigned_coding_site_loc = lab

    queue.add(
        Job(
            target=fn,
            name="ASSIGN LOC LAB: {} -> {}".format(submitted_data.qa_filename, lab),
            args=[submitted_data, lab],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_lab_emo", methods=["GET", "POST"])
def send_to_lab_emo():
    global datastore
    coding_form = CodingForm()
    submitted_data = datastore.find_submission(coding_form.ready_for_coding.data)
    lab = datastore.find_lab(coding_form.lab_list.data)

    def fn(x, lab):
        # Download the coded QA file:

        print(constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename)
        qa_file = bridge.box.get_file(
            constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename
        )

        if not qa_file:
            raise Exception("No completed QA file")

        bridge.box.download_file(qa_file, constants.TMP_DIR)
        output_file = DatavyuTemplateFactory.generate_emo_file(
            x, constants.TMP_DIR + "/" + x.qa_filename
        )
        print(
            "Uploading {} to {}".format(
                output_file, constants.PRI_CODING_DIR.format("emo", lab)
            )
        )
        bridge.transfer_file_to_box(
            output_file, constants.PRI_CODING_DIR.format("emo", lab), makedirs=True
        )
        x.assigned_coding_site_emo = lab

    queue.add(
        Job(
            target=fn,
            name="ASSIGN EMO LAB: {} -> {}".format(submitted_data.qa_filename, lab),
            args=[submitted_data, lab],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_lab_tra", methods=["GET", "POST"])
def send_to_lab_tra():
    global datastore
    coding_form = TraCodingForm()
    submitted_data = datastore.find_submission(coding_form.ready_for_coding.data)
    lab = coding_form.lab_list.data

    def fn(x, lab):
        # Download the coded QA file:

        print(constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename)
        qa_file = bridge.box.get_file(
            constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename
        )
        if not qa_file:
            raise Exception("No completed QA file")

        bridge.box.download_file(qa_file, constants.TMP_DIR)
        output_file = DatavyuTemplateFactory.generate_tra_file(
            x, constants.TMP_DIR + "/" + x.qa_filename
        )
        print(
            "Uploading {} to {}".format(
                output_file, constants.PRI_CODING_DIR.format("tra", lab)
            )
        )
        bridge.transfer_file_to_box(
            output_file, constants.PRI_CODING_DIR.format("tra", lab), makedirs=True
        )
        x.assigned_coding_site_tra = lab

    queue.add(
        Job(
            target=fn,
            name="ASSIGN TRA LAB: {} -> {}".format(submitted_data.qa_filename, lab),
            args=[submitted_data, lab],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_lab_comm", methods=["GET", "POST"])
def send_to_lab_comm():
    global datastore
    coding_form = CodingForm()
    submitted_data = datastore.find_submission(coding_form.ready_for_coding.data)
    lab = datastore.find_lab(coding_form.lab_list.data)

    def fn(x, lab):
        # Download the coded QA file:

        print(constants.QA_CODED_DIR.format(x.site_id) + x.qa_filename)
        qa_file = bridge.box.get_file(
            constants.PRI_CODED_DIR.format(x.site_id, "tra")
            + x.coding_filename_prefix
            + "_tra.opf"
        )
        if not qa_file:
            raise Exception("No completed Tra file")

        bridge.box.download_file(qa_file, constants.TMP_DIR)
        output_file = DatavyuTemplateFactory.generate_com_file(
            x, constants.TMP_DIR + "/" + x.qa_filename
        )
        print(
            "Uploading {} to {}".format(
                output_file, constants.PRI_CODING_DIR.format("com", lab)
            )
        )
        bridge.comnsfer_file_to_box(
            output_file, constants.PRI_CODING_DIR.format("com", lab), makedirs=True
        )
        x.assigned_coding_site_com = lab

    queue.add(
        Job(
            target=fn,
            name="ASSIGN COMM LAB: {} -> {}".format(submitted_data.qa_filename, lab),
            args=[submitted_data, lab],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_rel_obj", methods=["GET", "POST"])
def send_to_rel_obj():
    global datastore
    video_coding_form = VideosCodedForm()
    submitted_data = datastore.find_submission(video_coding_form.videos_coded.data)

    def fn(x):
        x.ready_for_rel_obj = True

    queue.add(
        Job(
            target=fn,
            name="READY FOR OBJ REL: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_rel_loc", methods=["GET", "POST"])
def send_to_rel_loc():
    global datastore
    video_coding_form = VideosCodedForm()
    submitted_data = datastore.find_submission(video_coding_form.videos_coded.data)

    def fn(x):
        x.ready_for_rel_loc = True

    queue.add(
        Job(
            target=fn,
            name="READY FOR LOC REL: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_rel_emo", methods=["GET", "POST"])
def send_to_rel_emo():
    global datastore
    video_coding_form = VideosCodedForm()
    submitted_data = datastore.find_submission(video_coding_form.videos_coded.data)

    def fn(x):
        x.ready_for_rel_emo = True

    queue.add(
        Job(
            target=fn,
            name="READY FOR EMO REL: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_rel_trans", methods=["GET", "POST"])
def send_to_rel_trans():
    global datastore
    video_coding_form = VideosCodedForm()
    submitted_data = datastore.find_submission(video_coding_form.videos_coded.data)

    def fn(x):
        x.ready_for_rel_tra = True

    queue.add(
        Job(
            target=fn,
            name="READY FOR TRANS REL: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_rel_comm", methods=["GET", "POST"])
def send_to_rel_comm():
    global datastore
    video_coding_form = VideosCodedForm()
    submitted_data = datastore.find_submission(video_coding_form.videos_coded.data)

    def fn(x):
        x.ready_for_rel_com = True

    queue.add(
        Job(
            target=fn,
            name="READY FOR TRANS REL: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_gold_obj", methods=["GET", "POST"])
def send_to_gold_obj():
    rel_form = RelForm()
    global datastore
    submitted_data = datastore.find_submission(rel_form.ready_for_rel.data)

    def fn(x):
        x.moved_to_gold_obj = True

    queue.add(
        Job(
            target=fn,
            name="MOVE TO GOLD OBJ: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_gold_loc", methods=["GET", "POST"])
def send_to_gold_loc():
    rel_form = RelForm()
    global datastore
    submitted_data = datastore.find_submission(rel_form.ready_for_rel.data)

    def fn(x):
        x.moved_to_gold_loc = True

    queue.add(
        Job(
            target=fn,
            name="MOVE TO GOLD LOC: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_gold_emo", methods=["GET", "POST"])
def send_to_gold_emo():
    rel_form = RelForm()
    global datastore
    submitted_data = datastore.find_submission(rel_form.ready_for_rel.data)

    def fn(x):
        x.moved_to_gold_emo = True

    queue.add(
        Job(
            target=fn,
            name="MOVE TO GOLD EMO: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/send_to_gold_comm", methods=["GET", "POST"])
def send_to_gold_comm():
    rel_form = RelForm()
    global datastore
    submitted_data = datastore.find_submission(rel_form.ready_for_rel.data)

    def fn(x):
        x.moved_to_gold_com = True

    queue.add(
        Job(
            target=fn,
            name="MOVE TO GOLD TRANS: {}".format(submitted_data.qa_filename),
            args=[submitted_data],
            item=submitted_data,
        )
    )

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/queue_action", methods=["GET", "POST"])
def queue_action():
    queue_form = QueueForm()
    global queue
    if queue_form.submit_queue.data:
        # Execute queue
        queue.run()
        results = []
        for i, job in enumerate(queue.queued_jobs):
            if job.status == 0:
                results.append((i, " Completed"))
            else:
                results.append((i, job.error_msg))
        queue_form.results.choices = results

        # queue.clear()
        # Handle any errors that have occurred
    if queue_form.remove_item_queue.data:
        to_remove = queue_form.actions.data
        for i in queue.queued_jobs:
            if i.display_name == to_remove:
                queue.queued_jobs.remove(i)
                break
    if queue_form.cancel_queue:
        queue.clear()

    forms = create_forms()
    return render_template("index.html", forms=forms, queue=queue)


@app.route("/progress")
def progress():
    global queue

    print(queue.status)
    return Response("data:{}\n\n".format(queue.status), mimetype="text/event-stream")


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
        assets = bridge.db.get_assets_for_volume(site.vol_id)
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

    # Set up the DB/Box/Kobo bridge
    global datastore
    global bridge
    global queue

    print(os.getcwd())
    bridge = Bridge("env/config.toml")

    # Load the data if it exists, otherwise populate from
    # online resources
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "rb") as handle:
            datastore = pickle.load(handle)
    else:
        datastore.sites, datastore.labs, datastore.tra_names = get_labs(bridge)
        get_kobo_forms(bridge)
        get_submissions(datastore.sites, bridge, datastore)

        datastore.save(SAVE_FILE)

        for site_code in datastore.sites:
            print(datastore.sites[site_code].submissions.keys())
            for subj in datastore.sites[site_code].submissions:
                print(site_code, subj, datastore.sites[site_code].submissions[subj])

    # Create a server to show the data
    print("Checking for changes to coded videos...")
    bridge.box.update_coded_videos(datastore)
    datastore.save(SAVE_FILE)
    url = "http://localhost:5000"
    threading.Timer(1.25, lambda: webbrowser.open(url)).start()
    app.run()


if __name__ == "__main__":
    startup()
