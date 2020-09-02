import logging
import re
import typing
from pathlib import Path
from typing import Any, Dict, List, Text, Union

from rasa.nlu.constants import TEXT
from rasa.nlu.training_data.formats.readerwriter import (
    TrainingDataReader,
    TrainingDataWriter,
)
import rasa.utils.io as io_utils

if typing.TYPE_CHECKING:
    from rasa.nlu.training_data import TrainingData

logger = logging.getLogger(__name__)


# looks for pattern like:
# ##
# * intent/response_key
#   - response_text
NLG_MARKDOWN_MARKER_REGEX = re.compile(r"##\s*.*\n\*[^:]*\/.*\n\s*\t*\-.*")


class NLGMarkdownReader(TrainingDataReader):
    """Reads markdown training data containing NLG stories and creates a TrainingData object."""

    def __init__(self) -> None:
        self.responses = {}

    def reads(self, s: Text, **kwargs: Any) -> "TrainingData":
        """Read markdown string and create TrainingData object"""
        from rasa.nlu.training_data import TrainingData

        self.__init__()
        lines = s.splitlines()
        self.responses = self.process_lines(lines)
        return TrainingData(responses=self.responses)

    @staticmethod
    def process_lines(lines: List[Text]) -> Dict[Text, List[Dict[Text, Text]]]:

        responses = {}
        story_intent = None
        story_bot_utterances = []  # Keeping it a list for future additions

        for idx, line in enumerate(lines):

            line_num = idx + 1
            try:
                line = line.strip()
                if line == "":
                    continue
                elif line.startswith("#"):
                    # reached a new story block
                    if story_intent:
                        responses[story_intent] = story_bot_utterances
                        story_bot_utterances = []
                        story_intent = None

                elif line.startswith("-"):
                    # reach an assistant's utterance

                    # utterance might have '-' itself, so joining them back if any
                    utterance = "-".join(line.split("- ")[1:])
                    # utterance might contain escaped newlines that we want to unescape
                    utterance = utterance.replace("\\n", "\n")
                    story_bot_utterances.append({TEXT: utterance})

                elif line.startswith("*"):
                    # reached a user intent
                    story_intent = "*".join(line.split("* ")[1:])

                else:
                    # reached an unknown type of line
                    logger.warning(
                        f"Skipping line {line_num}. "
                        "No valid command found. "
                        f"Line Content: '{line}'"
                    )
            except Exception as e:
                msg = f"Error in line {line_num}: {e}"
                logger.error(msg, exc_info=1)  # pytype: disable=wrong-arg-types
                raise ValueError(msg)

        # add last story
        if story_intent:
            responses[story_intent] = story_bot_utterances

        return responses

    @staticmethod
    def is_markdown_nlg_file(filename: Union[Text, Path]) -> bool:
        content = io_utils.read_file(filename)
        return re.search(NLG_MARKDOWN_MARKER_REGEX, content) is not None


class NLGMarkdownWriter(TrainingDataWriter):
    def dumps(self, training_data: "TrainingData") -> Text:
        """Transforms the NlG part of TrainingData object into a markdown string."""

        md = ""
        for intent, utterances in training_data.responses.items():
            md += "## \n"
            md += f"* {intent}\n"
            for utterance in utterances:
                md += f"- {utterance.get('text')}\n"
            md += "\n"
        return md
