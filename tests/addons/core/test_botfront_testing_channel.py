
import pytest


# this is needed so that the tests included as code examples look better
from tests.addons.core.conftest import botfront_test_channel_test_data

def test_botframework_channel():
    from rasa_addons.core.channels.test_case import TestCaseInput
    for test_data in botfront_test_channel_test_data:
        input_channel = TestCaseInput({ "url": "http://127.0.0.1:3000/graphql"})
        result = input_channel.compare_step_lists(test_data.get("actual"), test_data.get("expected"))
        assert result == test_data.get("result")
