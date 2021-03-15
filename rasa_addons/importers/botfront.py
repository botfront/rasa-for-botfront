import logging
import os
from typing import Optional, Text, Union, List, Dict

from rasa.shared.core.domain import Domain, InvalidDomain
from rasa.shared.core.training_data.structures import StoryGraph
from rasa.shared.importers import utils
from rasa.shared.importers.importer import TrainingDataImporter
from rasa.shared.nlu.training_data.training_data import TrainingData
import rasa.shared.utils.io
import rasa.shared.data
from rasa.core.utils import get_file_hash

logger = logging.getLogger(__name__)


class BotfrontFileImporter(TrainingDataImporter):
    def __init__(
        self,
        config_file: Optional[Union[List[Text], Text]] = None,
        domain_path: Optional[Text] = None,
        training_data_paths: Optional[Union[List[Text], Text]] = None,
    ):
        self._domain_path = domain_path

        self._nlu_files = rasa.shared.data.get_data_files(
            training_data_paths, rasa.shared.data.is_nlu_file
        )
        self._story_files = rasa.shared.data.get_data_files(
            training_data_paths, rasa.shared.data.is_story_file
        )

        self.core_config = {}
        self.nlu_config = {}
        if config_file:
            if not isinstance(config_file, list):
                config_file = [config_file]
            for file in config_file:
                if not os.path.exists(file):
                    continue
                config = rasa.shared.utils.io.read_config_file(file)
                lang = config["language"]
                self.core_config = {"policies": config["policies"]}
                self.nlu_config[lang] = {
                    "pipeline": config["pipeline"],
                    "language": lang,
                }

    def path_for_nlu_lang(self, lang) -> List[Text]:
        if len(self.nlu_config.keys()) < 2:
            return self._nlu_files
        return [x for x in self._nlu_files if f"nlu/{lang}" in x or f"nlu-{lang}" in x]

    async def get_config(self) -> Dict:
        return self.core_config

    async def get_nlu_config(self, languages=True) -> Dict:
        if not isinstance(languages, list):
            languages = self.nlu_config.keys()
        return {
            lang: self.nlu_config[lang] if lang in languages else False
            for lang in self.nlu_config.keys()
        }

    async def get_stories(
        self,
        template_variables: Optional[Dict] = None,
        use_e2e: bool = False,
        exclusion_percentage: Optional[int] = None,
    ) -> StoryGraph:

        return await utils.story_graph_from_paths(
            self._story_files,
            await self.get_domain(),
            template_variables,
            use_e2e,
            exclusion_percentage,
        )

    async def get_stories_hash(self):
        # Use a file hash of stories file to figure out Core fingerprint, instead of
        # storygraph object hash which is unstable
        if isinstance(self._story_files, list) and len(self._story_files):
            return get_file_hash(self._story_files[0])
        return 0

    async def get_nlu_data(self, languages=True) -> Dict[Text, TrainingData]:
        language = None
        if isinstance(languages, str):
            language = languages
            languages = [language]
        if not isinstance(languages, list):
            languages = self.nlu_config.keys()
        td = {}
        for lang in languages:
            try:
                td[lang] = utils.training_data_from_paths(
                    self.path_for_nlu_lang(lang), lang,
                )
            except ValueError as e:
                if str(e).startswith("Unknown data format"):
                    td[lang] = TrainingData()
        if language:
            return td.get(language, TrainingData())
        return td

    async def get_domain(self) -> Domain:
        domain = Domain.empty()
        if not self._domain_path:
            return domain
        try:
            domain = Domain.load(self._domain_path)
            domain.check_missing_templates()
        except Exception as e:
            logger.error(e)
        finally:
            return domain
