from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os

import requests
import simplejson
from rasa_nlu.components import Component
from typing import Any
from typing import List
from typing import Optional
from typing import Text

from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.extractors import EntityExtractor
from rasa_nlu.extractors.duckling_extractor import (
    filter_irrelevant_matches, convert_duckling_format_to_rasa)
from rasa_nlu.model import Metadata
from rasa_nlu.training_data import Message

logger = logging.getLogger(__name__)


class DucklingCrfMerger(Component):
    """Merges Duckling and CRF entities"""

    name = "duckling_crf_merger"

    provides = []

    defaults = {
        "entities": None,
    }

    def __init__(self, component_config=None):
        # type: (Text, Optional[List[Text]]) -> None

        super(DucklingCrfMerger, self).__init__(component_config)

    @classmethod
    def create(cls, config):
        # type: (RasaNLUModelConfig) -> DucklingCrfMerger

        return DucklingCrfMerger(config.for_component(cls.name,  cls.defaults))

    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None
        print (self.component_config["entities"])
        crf_entities = filter(lambda e: e["extractor"] == "ner_crf" and e["entity"] in self.component_config["entities"].keys(), message.get("entities"))
        indices_to_remove = []
        for index, duck in enumerate(message.get("entities")):
            if duck["extractor"].startswith("ner_duckling"):
                # looking for CRF entities surrounding the duckling one matching config settings
                containing_crf = filter(lambda e: e["start"] <= duck["start"] and e["end"] >= duck["end"] and duck["entity"] in self.component_config["entities"][e["entity"]], crf_entities)
                # list -> single object
                containing_crf = containing_crf[0] if len(containing_crf) > 0 else None
                if containing_crf is not None:
                    # Add duckling value + additional infos
                    containing_crf["value"] = duck["value"]
                    containing_crf["additional_info"] = duck['additional_info']
                    indices_to_remove.append(index)

        # Remove merged duckling entities
        for i in sorted(indices_to_remove, reverse=True):
            del message.get("entities")[i]

    @classmethod
    def load(cls,
             model_dir=None,  # type: Text
             model_metadata=None,  # type: Metadata
             cached_component=None,  # type: Optional[DucklingCrfMerger]
             **kwargs  # type: **Any
             ):
        # type: (...) -> DucklingCrfMerger

        component_config = model_metadata.for_component(cls.name)
        return cls(component_config)
