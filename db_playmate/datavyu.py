"""
Datavyu module:
    Contains wrappers for interacting with pyvyu for processing of datavyu files
"""

import os
import pyvyu
import db_playmate.constants as constants
from db_playmate import app


class DatavyuTemplateFactory:
    """Factory for generation of datavyu templates"""

    def generate_qa_file(submission):
        app.logger.info(submission.asset)
        spreadsheet = pyvyu.Spreadsheet()
        spreadsheet.new_column(
            "PLAY_id", "play_id", "birthdate", "testdate", "language_1", "language_2"
        )
        spreadsheet.new_column(
            "qa_id",
            "site_id",
            "subjn",
            "qadate",
            "light_heavy_qa",
            "experimenter",
            "qa_coder",
        )
        spreadsheet.new_column("qa", "comment", "error", "source")
        spreadsheet.new_column("qa_comments", "comment")

        play_id = submission.play_id
        birthdate = submission.birthdate
        testdate = submission.testdate

        site_id = submission.site_id
        subjn = submission.subj_number

        spreadsheet.get_column("PLAY_id").new_cell(play_id, birthdate, testdate)
        spreadsheet.get_column("qa_id").new_cell("", site_id, subjn)

        output_filename = constants.TMP_DATA_DIR + os.sep + submission.qa_filename

        app.logger.info(output_filename)

        # Create tmpdir if needed
        os.makedirs(constants.TMP_DATA_DIR, exist_ok=True)
        pyvyu.save_opf(
            spreadsheet, output_filename, True, "PLAY_id", "qa_id", "qa", "qa_comments",
        )

        return output_filename

    def generate_tra_file(submission, qa_file):
        tra_spreadsheet = pyvyu.load_opf(qa_file)
        tra_spreadsheet.new_column("transcribe", "source_mc", "content")
        tra_spreadsheet.new_column("transcribe_clean", "source_mc", "content")
        tra_spreadsheet.new_column(
            "tra_id",
            "transcriber",
            "date_tra",
            "light_heavy_qa",
            "qa_coder",
            "qa_date",
        )
        tra_spreadsheet.new_column("tra_comments", "source_mc", "comment")
        tra_spreadsheet.new_column("missing_child", "error")
        tra_spreadsheet.new_column(
            "PLAY_id", "play_id", "birthdate", "testdate", "language_1", "language_2"
        )

        tra_spreadsheet.new_column(
            "transcribeQA",
            "OnsetError",
            "SpeakerError",
            "ParsingError",
            "ContentError",
            "MissingExtraUtterance",
        )
        output_filename = "{}/{}_tra.opf".format(
            constants.TMP_DATA_DIR, submission.coding_filename_prefix
        )
        # Create tmpdir if needed
        os.makedirs(constants.TMP_DATA_DIR, exist_ok=True)
        pyvyu.save_opf(
            tra_spreadsheet,
            output_filename,
            True,
            "PLAY_id",
            "transcribe",
            "transcribe_clean",
            "transcribeQA",
            "tra_id",
            "tra_comments",
            "missing_child",
        )
        return output_filename

    def generate_com_file(submission, tra_file):
        # TODO get the correct columns here
        com_spreadsheet = pyvyu.load_opf(tra_file)

        # Implement the splitmomchild script
        tra_column = com_spreadsheet.get_column("transcribe_clean")

        momspeech = com_spreadsheet.new_column("momspeech", "content")
        childvoc = com_spreadsheet.new_column("childvoc", "content")

        # Implement create_momchild_utterancetype... script
        momutter = com_spreadsheet.new_column(
            "momutterancetype",
            "directives_look_l_do_d_comm_c",
            "prohibitions_p",
            "provideinfo_i_maintainengage_m",
            "read_r_sing_s",
            "filleraffirmation_f",
            "unintell_x_notchild_z",
        )
        childutter = com_spreadsheet.new_column(
            "childutterancetype",
            "language-s-w",
            "langlike-b-v",
            "crygrunt-c-g",
            "unintell-x",
        )

        for cell in tra_column.cells:
            if cell.get_code("source_mc") == "m":
                nc = momspeech.new_cell()
                nc.change_code("onset", cell.get_code("onset"))
                nc.change_code("offset", cell.get_code("offset"))
                nc.change_code("content", cell.get_code("content"))
                nc = momutter.new_cell()
                nc.change_code("onset", cell.get_code("onset"))
                nc.change_code("offset", cell.get_code("offset"))
            if cell.get_code("source_mc") == "c":
                nc = childvoc.new_cell()
                nc.change_code("onset", cell.get_code("onset"))
                nc.change_code("offset", cell.get_code("offset"))
                nc.change_code("content", cell.get_code("content"))
                nc = childutter.new_cell()
                nc.change_code("onset", cell.get_code("onset"))
                nc.change_code("offset", cell.get_code("offset"))

        output_filename = "{}/{}_com.opf".format(
            constants.TMP_DATA_DIR, submission.coding_filename_prefix
        )
        # Create tmpdir if needed
        os.makedirs(constants.TMP_DATA_DIR, exist_ok=True)
        pyvyu.save_opf(
            com_spreadsheet,
            output_filename,
            True,
            "PLAY_id",
            "tra_id",
            "transcribe",
            "transcribe_clean",
            "tra_comments",
            "momspeech",
            "childvoc",
            "momutterancetype",
            "childutterancetype",
            "missing_child",
        )
        return output_filename

    def generate_emo_file(submission, qa_file):
        emo_spreadsheet = pyvyu.load_opf(qa_file)
        emo_spreadsheet = pyvyu.Spreadsheet()
        emo_spreadsheet.new_column("childemotion", "emotion_pn")
        emo_spreadsheet.new_column(
            "emo_id", "lab_id", "pri_coder", "date_pri", "rel_coder", "rel_date"
        )
        emo_spreadsheet.new_column("momemotion", "emotion_pn")
        emo_spreadsheet.new_column("emo_comments", "source_mc", "comment")
        emo_spreadsheet.new_column("missing_child", "error")
        emo_spreadsheet.new_column(
            "PLAY_id", "play_id", "birthdate", "testdate", "language_1", "language_2"
        )

        output_filename = "{}/{}_emo.opf".format(
            constants.TMP_DATA_DIR, submission.coding_filename_prefix
        )
        # Create tmpdir if needed
        os.makedirs(constants.TMP_DATA_DIR, exist_ok=True)
        pyvyu.save_opf(
            emo_spreadsheet,
            output_filename,
            True,
            "PLAY_id",
            "momemotion",
            "emo_id",
            "emo_comments",
            "childemotion",
            "missing_child",
        )
        return output_filename

    def generate_obj_file(submission, qa_file):
        obj_spreadsheet = pyvyu.load_opf(qa_file)
        obj_spreadsheet.new_column("child_obj", "obj")
        obj_spreadsheet.new_column(
            "obj_id", "lab_id", "pri_coder", "date_pri", "rel_coder", "rel_date"
        )
        obj_spreadsheet.new_column("momobj", "obj")
        obj_spreadsheet.new_column("obj_comments", "source_mc", "comment")
        obj_spreadsheet.new_column("missing_child", "error")
        obj_spreadsheet.new_column(
            "PLAY_id", "play_id", "birthdate", "testdate", "language_1", "language_2"
        )

        output_filename = "{}/{}_obj.opf".format(
            constants.TMP_DATA_DIR, submission.coding_filename_prefix
        )
        app.logger.info(output_filename)

        # Create tmpdir if needed
        os.makedirs(constants.TMP_DATA_DIR, exist_ok=True)
        pyvyu.save_opf(
            obj_spreadsheet,
            output_filename,
            True,
            "PLAY_id",
            "momobj",
            "obj_id",
            "obj_comments",
            "child_obj",
            "missing_child",
        )
        return output_filename

    def generate_loc_file(submission, qa_file):
        loc_spreadsheet = pyvyu.load_opf(qa_file)
        loc_spreadsheet.new_column("momloc", "loc_lf")
        loc_spreadsheet.new_column(
            "loc_id", "lab_id", "pri_coder", "date_pri", "rel_coder", "rel_date"
        )
        loc_spreadsheet.new_column("loc_comments", "source_mc", "comment")
        loc_spreadsheet.new_column("child_loc", "loc_lfmdr")
        loc_spreadsheet.new_column("missing_child", "error")
        loc_spreadsheet.new_column(
            "PLAY_id", "play_id", "birthdate", "testdate", "language_1", "language_2"
        )
        output_filename = "{}/{}_loc.opf".format(
            constants.TMP_DATA_DIR, submission.coding_filename_prefix
        )

        # Create tmpdir if needed
        os.makedirs(constants.TMP_DATA_DIR, exist_ok=True)
        pyvyu.save_opf(
            loc_spreadsheet,
            output_filename,
            True,
            "PLAY_id",
            "momloc",
            "loc_id",
            "loc_comments",
            "child_loc",
            "missing_child",
        )
        return output_filename

    def generate_rel_file(submission, coding_pass):
        # TODO once we get the rel scripts
        site = getattr(submission, "assigned_coding_site_" + coding_pass)
        d = constants.TMP_DATA_DIR
        spreadsheet = pyvyu.load_opf(
            d + "/" + submission.coding_filename_prefix + "_" + coding_pass + ".opf"
        )
        all_columns = []
        for col in spreadsheet.get_column_list():
            col = spreadsheet.get_column(col)
            spreadsheet.new_column("rel_" + col.name, *col.codelist)
        output_filename = "{}/{}_{}_rel.opf".format(
            constants.TMP_DATA_DIR, submission.coding_filename_prefix, coding_pass
        )
        os.makedirs(constants.TMP_DATA_DIR, exist_ok=True)
        pyvyu.save_opf(spreadsheet, output_filename, True, *spreadsheet.columns.keys())
        return output_filename

    def combine_files(output_filename, *passes):
        """
        Combines OPF files listed in passes

        passes: list of filenames that have already been locally downloaded
                from box.
        """
        all_columns = {}
        for x in passes:
            sp = pyvyu.load_opf(x)
            column_list = sp.get_column_list()
            for c in column_list:
                all_columns[c] = sp.get_column(c)
        sp = pyvyu.Spreadsheet()
        sp.name = output_filename
        sp.columns = all_columns
        pyvyu.save_opf(sp, output_filename, True, *all_columns.keys())
        return output_filename
