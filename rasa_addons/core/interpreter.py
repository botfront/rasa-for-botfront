from typing import Text, Dict, Any, Optional
import rasa.core.interpreter
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.nlu.interpreter import NaturalLanguageInterpreter


class MultilingualNLUInterpreter(NaturalLanguageInterpreter):
    def __init__(
        self,
        model_directory: Dict[Text, Optional[Text]],
        config_file: Optional[Text] = None,
        lazy_init: bool = False,
    ):
        self.lazy_init = lazy_init
        self.config_file = config_file
        self.interpreters = {
            lang: rasa.core.interpreter.create_interpreter(model_path)
            for lang, model_path in model_directory.items()
        }

    async def parse(
        self,
        text: Text,
        message_id: Optional[Text] = None,
        tracker: DialogueStateTracker = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[Text, Any]:
        fallback_language_slot = (
            tracker.slots.get("fallback_language") if tracker else None
        )
        fallback_language = (
            fallback_language_slot.initial_value if fallback_language_slot else None
        )
        lang = (metadata or {}).get("language") or fallback_language
        if lang is None:
            raise Exception("No language specified.")
        interpreter = self.interpreters.get(lang)
        return await interpreter.parse(text)
