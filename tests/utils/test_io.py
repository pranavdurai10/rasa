import os
from pathlib import Path

import pytest
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError

import rasa.shared.utils.io
import rasa.utils.io as io_utils


@pytest.mark.parametrize("file, parents", [("A/test.md", "A"), ("A", "A")])
def test_file_in_path(file, parents):
    assert io_utils.is_subdirectory(file, parents)


@pytest.mark.parametrize(
    "file, parents", [("A", "A/B"), ("B", "A"), ("A/test.md", "A/B"), (None, "A")]
)
def test_file_not_in_path(file, parents):
    assert not io_utils.is_subdirectory(file, parents)


@pytest.mark.parametrize("actual_path", ["", "file.md", "file"])
def test_file_path_validator_with_invalid_paths(actual_path):
    test_error_message = actual_path

    validator = io_utils.file_type_validator([".yml"], test_error_message)

    document = Document(actual_path)
    with pytest.raises(ValidationError) as e:
        validator.validate(document)

    assert e.value.message == test_error_message


@pytest.mark.parametrize("actual_path", ["domain.yml", "lala.yaml"])
def test_file_path_validator_with_valid_paths(actual_path):
    validator = io_utils.file_type_validator([".yml", ".yaml"], "error message")

    document = Document(actual_path)
    # If the path is valid there shouldn't be an exception
    assert validator.validate(document) is None


@pytest.mark.parametrize("user_input", ["", "   ", "\t", "\n"])
def test_non_empty_text_validator_with_empty_input(user_input):
    test_error_message = "enter something"

    validator = io_utils.not_empty_validator(test_error_message)

    document = Document(user_input)
    with pytest.raises(ValidationError) as e:
        validator.validate(document)

    assert e.value.message == test_error_message


@pytest.mark.parametrize("user_input", ["utter_greet", "greet", "Hi there!"])
def test_non_empty_text_validator_with_valid_input(user_input):
    validator = io_utils.not_empty_validator("error message")

    document = Document(user_input)
    # If there is input there shouldn't be an exception
    assert validator.validate(document) is None


def test_create_validator_from_callable():
    def is_valid(user_input) -> None:
        return user_input == "this passes"

    error_message = "try again"

    validator = io_utils.create_validator(is_valid, error_message)

    document = Document("this passes")
    assert validator.validate(document) is None

    document = Document("this doesn't")
    with pytest.raises(ValidationError) as e:
        validator.validate(document)

    assert e.value.message == error_message


def test_write_json_file(tmp_path: Path):
    expected = {"abc": "dasds", "list": [1, 2, 3, 4], "nested": {"a": "b"}}
    file_path = str(tmp_path / "abc.txt")

    io_utils.dump_obj_as_json_to_file(file_path, expected)
    assert rasa.shared.utils.io.read_json_file(file_path) == expected


def test_write_utf_8_yaml_file(tmp_path: Path):
    """This test makes sure that dumping a yaml doesn't result in Uxxxx sequences
    but rather directly dumps the unicode character."""

    file_path = str(tmp_path / "test.yml")
    data = {"data": "amazing 🌈"}

    rasa.shared.utils.io.write_yaml(data, file_path)
    assert rasa.shared.utils.io.read_file(file_path) == "data: amazing 🌈\n"


def test_create_directory_if_new(tmp_path: Path):
    directory = str(tmp_path / "a" / "b")
    io_utils.create_directory(directory)

    assert os.path.exists(directory)


def test_create_directory_if_already_exists(tmp_path: Path):
    # This should not throw an exception
    io_utils.create_directory(str(tmp_path))
    assert True


def test_create_directory_for_file(tmp_path: Path):
    file = str(tmp_path / "dir" / "test.txt")

    io_utils.create_directory_for_file(str(file))
    assert not os.path.exists(file)
    assert os.path.exists(os.path.dirname(file))
