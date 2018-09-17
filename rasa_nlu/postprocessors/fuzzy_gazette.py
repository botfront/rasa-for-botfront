from typing import Any
from typing import List
from typing import Dict

from rasa_nlu.accor_fuzzy.fuzzy import Fuzzy
from rasa_nlu.components import Component
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.training_data import Message, TrainingData

# TODO: get key/values from training data

class FuzzyGazette(Component):
    name = "fuzzy_gazette"

    provides = ["entities", "additional_info"]

    defaults = {
        "minimum_score": 80,
        "max_num_suggestions": 5,
    }

    def __init__(self, component_config=None, gazette=None):
        # type: (RasaNLUModelConfig, Dict) -> None

        super(FuzzyGazette, self).__init__(component_config)
        self.gazette = gazette if gazette else {}


    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None

        fuzzy = Fuzzy('/Users/theodoretomalty/mrbot/rasa_nlu/rasa_nlu/accor_fuzzy/FullNameHotel.txt')
        entities = message.get("entities", [])

        for entity in entities:
            top_matches = fuzzy.find_matches(entity["value"])[:self.component_config.get("max_num_suggestions")]
            top_matches.sort(key=lambda x: x[1])
            primary, score = top_matches.pop() if len(top_matches) else (None, None)

            if primary is not None and score > self.component_config.get("minimum_score"):
                entity["entity"] = "hotel_name"
                entity["value"] = primary

                entity["additional_info"] = [{"value": value, "score": num} for value, num in top_matches]

        message.set("entities", entities)

    def train(self, training_data, config, **kwargs):
        # type: (TrainingData, RasaNLUModelConfig, **Any) -> None

        self._load_gazette(training_data.gazette)

    def _load_gazette(self, gazette):
        # type: (Dict) -> None

        for name, table in gazette.items():
            if name in self.gazette:
                self.gazette[name] += table
            else:
                self.gazette[name] = table