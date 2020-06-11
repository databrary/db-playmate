import io
import logging as log
import pytest
from db_playmate.kobo import Kobo, Form


@pytest.fixture(scope="session")
def kobo(configs):
    log.debug(configs)
    burl = configs["kobo"]["base_url"]
    token = configs["kobo"]["auth_token"]
    log.debug("Initializing kobo...")
    kobo = Kobo(base_url=burl, token=token)

    # check proper attributes are set
    assert kobo.base_url == burl
    assert kobo.token == token
    assert kobo.headers is not None
    assert kobo.forms is not None

    return kobo


def test_kobo(kobo):
    assert kobo.forms is not None


def test_get_form(kobo, example_form_id):
    assert kobo.get_form(form_id=example_form_id) is not None


def test_form_parse(example_form):
    f = Form(example_form)


def test_question():
    pass


def test_submission():
    pass


def test_form_to_csv(example_form, example_submissions):
    f = Form(example_form)
    for s in example_submissions:
        f.add_submission(data=s)

    csv = io.StringIO()
    f.to_csv(csv)
    log.info(csv.getvalue())
    f.to_csv(open("test.csv", "w+"))


def test_save_to_csv(kobo, output_folder):
    """Get assets from KoboToolbox and save all form submissions as csv files."""
    for form_id, form in kobo.forms.items():
        fn = form.name + ".csv"
        fp = output_folder.joinpath(fn)
        with open(fp, "w+") as outfile:
            form.to_csv(outfile)
