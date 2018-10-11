from typing import Any

from rasa_nlu.components import Component
from rasa_nlu.training_data import Message

from requests_futures.sessions import FuturesSession


class ApiLog(Component):
    name = 'api_log'

    defaults = {
        'url': '0.0.0.0',
        'model': None,
        'project': None,
    }

    def __init__(self, component_config=None):
        super(ApiLog, self).__init__(component_config)
        assert 'url' in component_config, 'You must specify the url to use the api_log component'

    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None

        session = FuturesSession()

        output = self._message_dict(message)
        model = self.component_config.get('model', False)
        if model:
            output['modelId'] = model


        session.post(self.component_config.get('url'), json=output)

    @staticmethod
    def _message_dict(message):
        obj = {
            'text': '',
            'intent': {
                'name': 'none',
                'confidence': 0,
            },
            'entities': [],
        }
        obj.update(message.as_dict(only_output_properties=True))

        intent = obj['intent']
        obj.update({
            'intent': intent['name'],
            'confidence': intent['confidence'],
        })

        return obj