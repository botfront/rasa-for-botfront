import json
import logging
from typing import Dict
from unittest.mock import patch, MagicMock, Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from aiohttp import ClientTimeout
from aioresponses import aioresponses
from sanic import Sanic

import rasa.core.run
from rasa.core import utils
from rasa.core.channels import RasaChatInput, console
from rasa.core.channels.channel import UserMessage
from rasa.core.channels.rasa_chat import (
    JWT_USERNAME_KEY,
    CONVERSATION_ID_KEY,
    INTERACTIVE_LEARNING_PERMISSION,
)
from rasa.core.channels.telegram import TelegramOutput
from rasa.utils.endpoints import EndpointConfig
from tests.core import utilities

# this is needed so that the tests included as code examples look better
from tests.utilities import json_of_latest_request, latest_request
from tests.addons.core.conftest import botfront_test_channel_test_data

def test_botframework_channel():
    from rasa_addons.core.channels.test_case import TestCaseInput
    for test_data in botfront_test_channel_test_data:
        input_channel = TestCaseInput({ "url": "http://127.0.0.1:3000/graphql"})
        result = input_channel.compare_step_lists(test_data.get("actual"), test_data.get("expected"))
        assert result == test_data.get("result")



