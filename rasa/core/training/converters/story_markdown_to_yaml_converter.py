import asyncio
from pathlib import Path
from typing import Text

from rasa.cli.utils import print_success, print_warning
from rasa.constants import DOCS_URL_RULES
from rasa.core.training.story_reader.markdown_story_reader import MarkdownStoryReader
from rasa.core.training.story_writer.yaml_story_writer import YAMLStoryWriter
from rasa.utils.tensorflow.converter import TrainingDataConverter


class StoryMarkdownToYamlConverter(TrainingDataConverter):
    @classmethod
    def filter(cls, source_path: Path) -> bool:
        """Checks if the given training data file contains Core data in `Markdown`
        format and can be converted to `YAML`.

        Args:
            source_path: Path to the training data file.

        Returns:
            `True` if the given file can be converted, `False` otherwise
        """
        return MarkdownStoryReader.is_markdown_story_file(source_path)

    @classmethod
    def convert_and_write(cls, source_path: Path, output_path: Path) -> None:
        """Converts the given training data file and saves it to the output directory.

        Args:
            source_path: Path to the training data file.
            output_path: Path to the output directory.
        """
        from rasa.core.training.story_reader.yaml_story_reader import KEY_ACTIVE_LOOP

        output_core_path = cls.generate_path_for_converted_training_data_file(
            source_path, output_path
        )

        reader = MarkdownStoryReader(unfold_or_utterances=False)
        writer = YAMLStoryWriter()

        loop = asyncio.get_event_loop()
        steps = loop.run_until_complete(reader.read_from_file(source_path))

        if YAMLStoryWriter.stories_contain_loops(steps):
            print_warning(
                f"Training data file '{source_path}' contains forms. "
                f"Any 'form' events will be converted to '{KEY_ACTIVE_LOOP}' events. "
                f"Please note that in order for these stories to work you still "
                f"need the 'FormPolicy' to be active. However the 'FormPolicy' is "
                f"deprecated, please consider switching to the new 'RulePolicy', "
                f"for which you can find the documentation here: {DOCS_URL_RULES}."
            )

        writer.dump(output_core_path, steps)

        print_success(f"Converted Core file: '{source_path}' >> '{output_core_path}'.")

    @classmethod
    def converted_file_suffix(cls) -> Text:
        """Returns suffix that should be appended to the converted training data file.
        """
        return "_converted.yml"
