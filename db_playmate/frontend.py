import os
import pickle
from flask import Flask, render_template
from sheets import read_master
from data_model import Datastore, Submission
from bridge import Bridge
from threading import Thread
from wtforms.fields import SelectMultipleField, SubmitField
from flask_wtf import FlaskForm



SAVE_FILE = "env/db_playmate.pickle"

global server
app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'
global datastore
datastore = Datastore()

class InDbForm(FlaskForm):
    in_databrary = SelectMultipleField("In Databrary")
    submit_send_to_qa = SubmitField("Send to QA")

class QAForm(FlaskForm):
    ready_for_qa = SelectMultipleField("Ready For QA")
    submit_send_to_coding = SubmitField("Send to Coding")
    submit_send_to_silver = SubmitField("Send to Silver")

class CodingForm(FlaskForm):
    ready_for_coding = SelectMultipleField("Ready for Coding")
    lab_list = SelectMultipleField("List of Labs")
    submit_send_to_lab = SubmitField("Send to Selected Lab")

class VideosCodedForm(FlaskForm):
    videos_coded = SelectMultipleField("Coded Videos")
    videos_not_coded = SelectMultipleField("Video Being Coded")
    submit_send_to_rel = SubmitField("Send to Rel")

class RelForm(FlaskForm):
    ready_for_rel = SelectMultipleField("Ready for Rel")
    submit_send_to_gold = SubmitField("Send to GOLD")
    gold = SelectMultipleField("In GOLD")


#  def populate_main_page():
    #  global datastore
    #  ready_for_qa = [x for site in datastore.sites.values() for x in site.submissions.values()]
    #  print(ready_for_qa)
    #  return render_template('index.html')

def create_forms():
    global datastore
    in_db_form = InDbForm({"width": "200px"})
    in_db = [(x.id, x.name) for site in datastore.sites.values() for x in site.submissions.values() if x.ready_for_qa == False]
    in_db_form.in_databrary.choices = in_db if len(in_db) > 0 else [('-','-')]


    qa_form = QAForm()
    qa = [(x.id, x.name) for site in datastore.sites.values() for x in site.submissions.values() if x.ready_for_qa == True and x.ready_for_coding == False]
    qa_form.ready_for_qa.choices = qa if len(qa) > 0 else [('-','-')]


    coding_form = CodingForm()
    coding_videos = [(x.id, x.name) for site in datastore.sites.values() for x in site.submissions.values() if x.ready_for_coding == True and x.assigned_coding_site is None]
    coding_form.ready_for_coding.choices = coding_videos
    lab_list = [(x.lab_code, x.lab_code) for x in datastore.labs]
    coding_form.lab_list.choices = lab_list

    video_coding_form = VideosCodedForm()
    v_coding_done = [(x.id, x.name) for site in datastore.sites.values() for x in site.submissions.values() if x.primary_coding_finished and x.ready_for_rel == False]
    v_coding_not_done = [(x.id, x.name) for site in datastore.sites.values() for x in site.submissions.values() if x.primary_coding_finished == False and x.assigned_coding_site is not None]
    video_coding_form.videos_coded.choices = v_coding_done
    video_coding_form.videos_not_coded.choices = v_coding_not_done

    rel_form = RelForm()
    ready_for_rel = [(x.id, x.name) for site in datastore.sites.values() for x in site.submissions.values() if x.ready_for_rel and x.rel_coding_finished == False]
    rel_form.ready_for_rel.choices = ready_for_rel
    gold_videos = [(x.id, x.name) for site in datastore.sites.values() for x in site.submissions.values() if x.moved_to_gold]
    rel_form.gold.choices = gold_videos

    return in_db_form, qa_form, coding_form, video_coding_form, rel_form



@app.route("/")
@app.route("/index.html", methods=["GET", "POST"])
def populate_main_page():
    global datastore
    in_db_form, qa_form, coding_form, video_coding_form, rel_form = create_forms()
    return render_template('index.html', in_db_form=in_db_form, qa_form=qa_form, coding_form=coding_form, video_coding_form=video_coding_form, rel_form=rel_form)


@app.route('/send_to_qa', methods=["GET", "POST"])
def send_to_qa():
    global datastore
    in_db_form = InDbForm()
    submitted_data = datastore.find_submission(in_db_form.in_databrary.data[0])
    submitted_data.ready_for_qa = True

    in_db_form, qa_form, coding_form, video_coding_form, rel_form = create_forms()
    return render_template('index.html', in_db_form=in_db_form, qa_form=qa_form, coding_form=coding_form, video_coding_form=video_coding_form, rel_form=rel_form)


@app.route('/send_to_coding', methods=["GET", "POST"])
def send_to_coding():
    global datastore
    qa_form = QAForm()
    submitted_data = datastore.find_submission(qa_form.ready_for_qa.data[0])
    submitted_data.ready_for_coding = True

    in_db_form, qa_form, coding_form, video_coding_form, rel_form = create_forms()
    return render_template('index.html', in_db_form=in_db_form, qa_form=qa_form, coding_form=coding_form, video_coding_form=video_coding_form, rel_form=rel_form)


@app.route('/send_to_lab', methods=["GET", "POST"])
def send_to_lab():
    global datastore
    coding_form = CodingForm()
    submitted_data = datastore.find_submission(coding_form.ready_for_coding.data[0])
    lab = datastore.find_lab(coding_form.lab_list.data[0])
    submitted_data.assigned_coding_site = lab

    in_db_form, qa_form, coding_form, video_coding_form, rel_form = create_forms()
    return render_template('index.html', in_db_form=in_db_form, qa_form=qa_form, coding_form=coding_form, video_coding_form=video_coding_form, rel_form=rel_form)


@app.route('/send_to_rel', methods=["GET", "POST"])
def send_to_rel():
    global datastore
    video_coding_form = VideosCodedForm()
    submitted_data = datastore.find_submission(video_coding_form.videos_coded.data[0])
    submitted_data.ready_for_rel = True

    in_db_form, qa_form, coding_form, video_coding_form, rel_form = create_forms()
    return render_template('index.html', in_db_form=in_db_form, qa_form=qa_form, coding_form=coding_form, video_coding_form=video_coding_form, rel_form=rel_form)


@app.route('/send_to_gold', methods=["GET", "POST"])
def send_to_gold():
    rel_form = RelForm()
    global datastore
    submitted_data = datastore.find_submission(rel_form.ready_for_rel.data[0])
    submitted_data.moved_to_gold = True

    in_db_form, qa_form, coding_form, video_coding_form, rel_form = create_forms()
    return render_template('index.html', in_db_form=in_db_form, qa_form=qa_form, coding_form=coding_form, video_coding_form=video_coding_form, rel_form=rel_form)


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
    global datastore
    global server

    bridge = Bridge("env/config.toml")

    # Load the data if it exists, otherwise populate from
    # online resources
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'rb') as handle:
            datastore = pickle.load(handle)
    else:
        datastore.sites, datastore.labs = get_labs(bridge)
        get_submissions(datastore.sites, bridge, datastore)

        print(datastore.sites.keys())
        # get_kobo_forms(bridge)
        datastore.save(SAVE_FILE)

        for site_code in datastore.sites:
            print(datastore.sites[site_code].submissions.keys())
            for subj in datastore.sites[site_code].submissions:
                print(site_code, subj, datastore.sites[site_code].submissions[subj])

    # Create a server to show the data
    app.run()



if __name__ == "__main__":
    startup()
