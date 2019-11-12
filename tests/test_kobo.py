def test_kobo(kobo, example_assets):
    assert example_assets == kobo._response


def test_get_form(kobo, example_submissions):
    assert example_submissions.cmp(kobo.forms["aGD5Q64T5zTQtakQaS8x55"]) == 0
