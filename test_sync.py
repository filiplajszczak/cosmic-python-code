import tempfile
from pathlib import Path
import shutil

import pytest

from sync import FileSystem, sync


class TestE2E:
    @staticmethod
    def test_when_a_file_exists_in_the_source_but_not_the_destination():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a very useful file"
            (Path(source) / "my-file").write_text(content)

            sync(source, dest)

            expected_path = Path(dest) / "my-file"
            assert expected_path.exists()
            assert expected_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)

    @staticmethod
    def test_when_a_file_has_been_renamed_in_the_source():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a file that was renamed"
            source_path = Path(source) / "source-filename"
            old_dest_path = Path(dest) / "dest-filename"
            expected_dest_path = Path(dest) / "source-filename"
            source_path.write_text(content)
            old_dest_path.write_text(content)

            sync(source, dest)

            assert old_dest_path.exists() is False
            assert expected_dest_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)


@pytest.fixture
def get_fakefs(mocker):
    def _get_fakefs(paths):
        return mocker.Mock(read=lambda path: paths[path])
    return _get_fakefs


def test_when_a_file_exists_in_the_source_but_not_the_destination(get_fakefs):
    fakefs = get_fakefs(
        {
            '/src': {"hash1": "fn1"},
            '/dst': {},
        }
    )

    sync('/src', '/dst', filesystem=fakefs)

    fakefs.copy.assert_called_once_with(Path("/src/fn1"), Path("/dst/fn1"))
    fakefs.move.assert_not_called()
    fakefs.delete.assert_not_called()


def test_when_a_file_has_been_renamed_in_the_source(get_fakefs):
    fakefs = get_fakefs(
        {
            '/src': {"hash1": "fn1"},
            '/dst': {"hash1": "fn2"},
        }
    )

    sync('/src', '/dst', filesystem=fakefs)

    fakefs.move.assert_called_once_with(Path("/dst/fn2"), Path("/dst/fn1"))
    fakefs.copy.assert_not_called()
    fakefs.delete.assert_not_called()
