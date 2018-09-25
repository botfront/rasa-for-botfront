import os

from typing import Any
from typing import Text
from typing import Dict
from typing import Optional

from rasa_nlu.components import Component
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.training_data import Message, TrainingData
from rasa_nlu.model import Metadata

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

FUZZY_GAZETTE_FILE = "fuzzy_gazette.json"


def _find_matches(query, gazette, mode="ratio", limit=5):
    output = {}
    for key, val in gazette.items():
        output[key] = process.extract(query, val, limit=limit, scorer=getattr(fuzz, mode))
    return output


def _find_entity_config(entity, config):
    for rep in config.get("entities", []):
        if entity["entity"] == rep["name"]:
            return rep

    return None


class FuzzyGazette(Component):
    name = "fuzzy_gazette"

    provides = ["entities"]

    defaults = {
        "extractors": ["ner_crf"],
        "max_num_suggestions": 5,
        "entities": [],
    }

    def __init__(self, component_config=None, gazette=None):
        # type: (RasaNLUModelConfig, Dict) -> None

        super(FuzzyGazette, self).__init__(component_config)
        self.gazette = gazette if gazette else {}

    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None

        self._load_config()
        entities = message.get("entities", [])
        limit = self.component_config.get("max_num_suggestions")

        for entity in entities:
            right_extractor = "extractor" in entity and entity["extractor"] in self.component_config["extractors"]
            config = _find_entity_config(entity, self.component_config)

            if not isinstance(entity["value"], str) or not right_extractor or config is None:
                continue

            matches = _find_matches(entity["value"], self.gazette, mode=config["mode"], limit=limit)
            top_matches = []
            for key, val in matches.items():
                for item in val:
                    top_matches.append((key, *item))
            top_matches.sort(key=lambda x: x[2])

            key, primary, score = top_matches[-1] if len(top_matches) else (None, None, None)

            if primary is not None and score > config["min_score"]:
                entity["entity"] = key
                entity["value"] = primary

                entity["gazette_best_matches"] = [{"entity": entity, "value": value, "score": num} for entity, value, num in top_matches]

        message.set("entities", entities)

    def train(self, training_data, config, **kwargs):
        # type: (TrainingData, RasaNLUModelConfig, **Any) -> None

        self._load_gazette_list(training_data.fuzzy_gazette)

    def persist(self, model_dir):
        # type: (Text) -> Optional[Dict[Text, Any]]

        if self.gazette:
            from rasa_nlu.utils import write_json_to_file
            file_name = os.path.join(model_dir, FUZZY_GAZETTE_FILE)

            write_json_to_file(file_name, self.gazette,
                               separators=(',', ': '))

        return {"gazette_file": FUZZY_GAZETTE_FILE}

    @classmethod
    def load(cls,
             model_dir=None,   # type: Optional[Text]
             model_metadata=None,   # type: Optional[Metadata]
             cached_component=None,   # type: Optional[Component]
             **kwargs  # type: **Any
             ):
        from rasa_nlu.utils import read_json_file

        meta = model_metadata.for_component(cls.name)
        file_name = meta.get("gazette_file", FUZZY_GAZETTE_FILE)
        path = os.path.join(model_dir, file_name)

        gazette = read_json_file(path)
        return FuzzyGazette(meta, gazette)

    def _load_gazette_list(self, gazette):
        # type: (Dict) -> None

        for item in gazette:
            name = item["value"]
            table = item["gazette"]
            if name in self.gazette:
                self.gazette[name] += table
            else:
                self.gazette[name] = table

    def _load_config(self):
        entities = []
        for rep in self.component_config.get("entities", []):
            assert "name" in rep, "Must provide the entity name for the gazette entity configuration: {}".format(rep)
            assert rep["name"] in self.gazette, "Could not find entity name {0} in gazette {1}".format(rep["name"], self.gazette)

            supported_properties = ["entities", "mode", "min_score"]
            defaults = [[], "ratio", 80]

            new_element = {"name": rep["name"]}
            for prop, default in zip(supported_properties, defaults):
                if prop not in rep:
                    new_element[prop] = default
                else:
                    assert isinstance(rep[prop], type(default)), "The type of {0} in {1} does not match the default".format(prop, rep["name"])
                    new_element[prop] = rep[prop]

            entities.append(new_element)

        self.component_config["entities"] = entities