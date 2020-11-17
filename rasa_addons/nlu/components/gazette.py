import os
import warnings
import rasa

from typing import Any, Text, Dict, Optional

import rasa.shared.utils.io
from rasa.nlu import utils
from rasa.nlu.components import Component
from rasa.nlu.config import RasaNLUModelConfig
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.nlu.model import Metadata

from fuzzy_matcher import process


class Gazette(Component):
    name = "Gazette"

    defaults = {"max_num_suggestions": 5, "entities": []}

    def __init__(
        self, component_config: Text = None, gazette: Optional[Dict] = None
    ) -> None:

        super(Gazette, self).__init__(component_config)
        self.gazette = gazette if gazette else {}
        if gazette:
            self._load_config()
        self.limit = self.component_config.get("max_num_suggestions")
        self.entities = self.component_config.get("entities", [])

    def process(self, message: Message, **kwargs: Any) -> None:

        entities = message.get("entities", [])
        new_entities = []

        for entity in entities:
            config = self._find_entity(entity, self.entities)
            if config is None or not isinstance(entity["value"], str):
                new_entities.append(entity)
                continue

            matches = process.extract(
                entity["value"],
                self.gazette.get(entity["entity"], []),
                limit=self.limit,
                scorer=config["mode"],
            )
            primary, score = matches[0] if len(matches) else (None, None)

            if primary is not None and score > config["min_score"]:
                entity["value"] = primary
                entity["gazette_matches"] = [
                    {"value": value, "score": num} for value, num in matches
                ]
                new_entities.append(entity)

        message.set("entities", new_entities)

    def train(
        self, training_data: TrainingData, cfg: RasaNLUModelConfig, **kwargs: Any
    ) -> None:
        gazette_dict = {}
        if hasattr(training_data, "gazette") and type(training_data.gazette) == list:
            for item in training_data.gazette:
                name = item["value"]
                table = item["gazette"]
                gazette_dict[name] = table
            self.gazette = gazette_dict

    def persist(self, file_name: Text, model_dir: Text) -> Optional[Dict[Text, Any]]:
        file_name = file_name + ".json"
        utils.write_json_to_file(os.path.join(model_dir, file_name), self.gazette, indent=4)

        return {"file": file_name}
    
    @classmethod
    def load(
        cls,
        component_meta: Dict[Text, Any],
        model_dir: Text = None,
        model_metadata: Metadata = None,
        cached_component: Optional["Gazette"] = None,
        **kwargs: Any
    ) -> "Gazette":
        try:
            file = os.path.join(model_dir, component_meta.get("file", "gazette.json"))
            return Gazette(component_meta, rasa.shared.utils.io.read_json_file(file))
        except:
            warnings.warn("Could not load gazette.")
            return Gazette(component_meta, None)

    @staticmethod
    def _find_entity(entity, entities):
        for rep in entities:
            if entity["entity"] == rep["name"]:
                return rep
        return None

    def _load_config(self):
        entities = []
        for rep in self.component_config.get("entities", []):
            assert (
                "name" in rep
            ), "Must provide the entity name for the gazette entity configuration: {}".format(
                rep
            )
            assert (
                rep["name"] in self.gazette
            ), "Could not find entity name {0} in gazette {1}".format(
                rep["name"], self.gazette
            )

            supported_properties = ["mode", "min_score"]
            defaults = ["ratio", 80]
            types = [str, int]

            new_element = {"name": rep["name"]}
            for prop, default, t in zip(supported_properties, defaults, types):
                if prop not in rep:
                    new_element[prop] = default
                else:
                    new_element[prop] = t(rep[prop])

            entities.append(new_element)

        self.component_config["entities"] = entities
