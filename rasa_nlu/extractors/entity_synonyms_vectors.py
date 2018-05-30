from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import operator
from rasa_nlu.components import Component
from typing import Any
from typing import List
from typing import Optional
from typing import Text

from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Metadata
from rasa_nlu.training_data import Message

logger = logging.getLogger(__name__)


class EntitySynonymsVectors(Component):
    """Filter entities wrt intent"""

    name = "ner_synonyms_vectors"
    provides = ["entities"]
    defaults = {
        "entities": {}
    }

    def __init__(self, component_config=None):
        # type: (Text, Optional[List[Text]]) -> None
        self.main_entities_spacy_docs = {}

        super(EntitySynonymsVectors, self).__init__(component_config)

    @classmethod
    def create(cls, config):
        # type: (RasaNLUModelConfig) -> DucklingCrfMerger

        return EntitySynonymsVectors(config.for_component(cls.name,  cls.defaults))

    def _init_main_entities_vectors(self, message):
        for key in self.component_config["entities"].keys():
            self.main_entities_spacy_docs[key] = [message.data["spacy_nlp"](exp) for exp in
                                                  self.component_config["entities"][key]]

    def _most_similar_entity_value(self, entity_name, synonym):
        similarities = [synonym.similarity(i) for i in self.main_entities_spacy_docs[entity_name]]
        max_index, max_value = max(enumerate(similarities), key=operator.itemgetter(1))
        return self.main_entities_spacy_docs[entity_name][max_index].text

    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None

        # initialize vectors
        if len(self.main_entities_spacy_docs) == 0:
            self._init_main_entities_vectors(message)

        # get relevant crf entities
        for e in message.get("entities"):
            if e["extractor"] == "ner_crf" and e["entity"] in self.component_config["entities"].keys():
                e["value"] = self._most_similar_entity_value(e["entity"], message.data["spacy_nlp"](e["value"]))

        print(message.get("entities"))

    @classmethod
    def load(cls,
             model_dir=None,  # type: Text
             model_metadata=None,  # type: Metadata
             cached_component=None,  # type: Optional[EntitySynonymsVectors]
             **kwargs  # type: **Any
             ):
        # type: (...) -> EntitySynonymsVectors

        component_config = model_metadata.for_component(cls.name)
        return cls(component_config)
