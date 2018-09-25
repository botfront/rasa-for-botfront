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


class FuzzyGazette(Component):
    name = "fuzzy_gazette"

    provides = ["entities", "additional_info"]

    defaults = {
        "minimum_score": 80,
        "max_num_suggestions": 5,
        "mode": "ratio"
    }

    def __init__(self, component_config=None, gazette=None):
        # type: (RasaNLUModelConfig, Dict) -> None

        super(FuzzyGazette, self).__init__(component_config)
        self.gazette = gazette if gazette else {}

    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None

        entities = message.get("entities", [])
        mode = self.component_config.get("mode")
        limit = self.component_config.get("max_num_suggestions")

        for entity in entities:
            matches = _find_matches(entity["value"], self.gazette, mode=mode, limit=limit)
            top_matches = []
            for key, val in matches.items():
                for item in val:
                    top_matches.append((key, *item))
            top_matches.sort(key=lambda x: x[2])

            key, primary, score = top_matches.pop() if len(top_matches) else (None, None, None)

            if primary is not None and score > self.component_config.get("minimum_score"):
                entity["entity"] = key
                entity["value"] = primary

                entity["additional_info"] = [{"entity": entity, "value": value, "score": num} for entity, value, num in top_matches]

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
        file_name = meta.get("synonyms_file", FUZZY_GAZETTE_FILE)
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