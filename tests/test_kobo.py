def test_kobo(kobo, example_assets):
    assert example_assets == kobo._response


def test_get_form(kobo, example_submissions):
    assert example_submissions.cmp(kobo.forms["aGD5Q64T5zTQtakQaS8x55"]) == 0


def test_question():
    from kobo.question import Question

    q = Question(hash(1), "What is your name?", label="name")
    assert str(q) == "name"

    q2 = Question(hash(2), "What is your age?")
    assert str(q2) == "What is your age?"

    assert q2 is not q
    assert not q.congruent_to(q2)

    q.merge(q2)
    assert all(k in q.sigs for k in q2.sigs)
