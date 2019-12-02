from db_playmate import __version__


def test_version():
    assert __version__ == "0.1.0"


def create_testdir(client):
    return client.create_folder("", "testdir")


def delete_testdir(client):
    return client.delete("testdir")


def test_box_folders(box_client):
    delete_testdir(box_client)
    x = create_testdir(box_client)
    assert x is not None

    x = box_client.create_folder("testdir/a", "b")
    assert x is None  # This should fail because a doesnt exist

    x = box_client.create_folder("testdir", "a")  # This should succeed
    assert x is not None and x.name == "a"

    x = box_client.create_folder("testdir/a", "b")
    assert x is not None and x.name == "b" and x.parent.name == "a"

    x = box_client.create_folders("testdir/b/c")
    assert x is not None and x.name == "c" and x.parent.name == "b"


def test_box_files(box_client, root_folder):
    x = box_client.get_folder("testdir")
    if x is None:
        x = box_client.create_folder("", "testdir")
        assert x is not None and x.name == "testdir"

    x = box_client.upload_file(root_folder.joinpath("./README.rst"), "testdir")
    assert x is not None and x.name == "README.rst" and x.parent.name == "testdir"

    x = box_client.move("testdir/README.rst", "testdir", "READYOU.rst")
    assert x is not None and x.name == "READYOU.rst" and x.parent.name == "testdir"

    x = box_client.copy("testdir/READYOU.rst", "testdir", "README.rst")
    assert x is not None and x.name == "README.rst" and x.parent.name == "testdir"

    x = box_client.delete("testdir/README.rst")
    assert x is True
