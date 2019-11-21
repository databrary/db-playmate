import logging as log


# TODO
def test_kobo(kobo, example_assets):
    assert example_assets == kobo._response


def test_get_form(kobo, example_submissions):
    pass


def test_form__parse(example_form):
    from db_playmate.kobo.form import Form

    f = Form(example_form)
    log.debug(f)


def test_question():
    pass


def test_submission():
    pass


def test_form_to_csv(example_form, example_submissions):
    from db_playmate.kobo.form import Form
    import io

    f = Form(example_form)
    for s in example_submissions:
        f.add_submission(data=s)

    csv = io.StringIO()
    f.to_csv(csv)
    log.info(csv.getvalue())
    f.to_csv(open("test.csv", "w+"))
