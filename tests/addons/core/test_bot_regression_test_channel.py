
import pytest
# this is needed so that the tests included as code examples look better
from rasa_addons.core.channels.bot_regression_test import BotRegressionTestInput

bot_regression_test_data = [
    {
        # bot_regression_test_data0: full match
        "expected": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
            { "action": "utter_step_one" },
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 14, "value": "second" }
            ]},
            { "action": "utter_step_two"},
        ],
        "actual": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
            { "metadata": { "template_name": "utter_step_one" }},
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 14, "value": "second" }
            ]},
            { "metadata": { "template_name": "utter_step_two" }},
        ],
        "result": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
            { "action": "utter_step_one" },
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 14, "value": "second" }
            ]},
            { "action": "utter_step_two"},
        ],
    },
    {
        # bot_regression_test_data1: intent mismatch
        "expected": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
        ],
        "actual": [
            { "user": "run step one", "intent": "step_two", "entities": [] },
        ],
        "result": [
            { "user": "run step one", "intent": "step_two", "entities": [], "theme": "actual" },
            { "user": "run step one", "intent": "step_one", "entities": [], "theme": "expected" },
        ],
    },
    {
        # bot_regression_test_data2: entity name mismatch
        "expected": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "expected_name", "start": 8, "end": 14, "value": "second" }
            ]},
        ],
        "actual": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "actual_name", "start": 8, "end": 14, "value": "second" }
            ]},
        ],
        "result": [
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "actual_name", "start": 8, "end": 14, "value": "second" }
                ],
                "theme": "actual",
            },
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "expected_name", "start": 8, "end": 14, "value": "second" }
                ],
                "theme": "expected",
            },
        ],
    },
    {
        # bot_regression_test_data3: entity value mismatch
        "expected": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 14, "value": "second" }
            ]},
        ],
        "actual": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 14, "value": "third" }
            ]},
        ],
        "result": [
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "index", "start": 8, "end": 14, "value": "third" }
                ],
                "theme": "actual",
            },
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "index", "start": 8, "end": 14, "value": "second" }
                ],
                "theme": "expected",
            },
        ],
    },
    {
        # bot_regression_test_data4: entity start mismatch
        "description": "entity start mismatch",
        "expected": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 14, "value": "second" }
            ]},
        ],
        "actual": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 9, "end": 14, "value": "second" }
            ]},
        ],
        "result": [
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "index", "start": 9, "end": 14, "value": "second" }
                ],
                "theme": "actual",
            },
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "index", "start": 8, "end": 14, "value": "second" }
                ],
                "theme": "expected",
            },
        ],
    },
    {
        # bot_regression_test_data5: entity end mismatch
        "description": "entity end mismatch",
        "expected": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 14, "value": "second" }
            ]},
        ],
        "actual": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 15, "value": "second" }
            ]},
        ],
        "result": [
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "index", "start": 8, "end": 15, "value": "second" }
                ],
                "theme": "actual",
            },
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "index", "start": 8, "end": 14, "value": "second" }
                ],
                "theme": "expected",
            },
        ],
    },
    { # bot_regression_test_data6: number of entities mismatch
        "description": "number of entities mismatch",
        "expected": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 14, "value": "second" }
            ]},
        ],
        "actual": [
            { "user": "run the second step", "intent": "step_two", "entities": [
                { "entity": "index", "start": 8, "end": 14, "value": "second" },
                { "entity": "other", "start": 0, "end": 3, "value": "run" },
            ]},
        ],
        "result": [
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "index", "start": 8, "end": 14, "value": "second" },
                    { "entity": "other", "start": 0, "end": 3, "value": "run" }
                ],
                "theme": "actual",
            },
            {
                "user": "run the second step",
                "intent": "step_two",
                "entities": [
                    { "entity": "index", "start": 8, "end": 14, "value": "second" }
                ],
                "theme": "expected",
            },
        ],
    },
    {
        # bot_regression_test_data7: action mismatch
        "description": "action mismatch",
        "expected": [
            { "action": "utter_step_one" },
        ],
        "actual": [
            { "metadata": { "template_name": "utter_step_two" }},
        ],
        "result": [
            { "action": "utter_step_two", "theme": "actual" },
            { "action": "utter_step_one", "theme": "expected" },
        ],
    },
    {
        # bot_regression_test_data8:extra actual step
        "description": "number of steps mismatch",
        "expected": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
            { "action": "utter_step_one" },
        ],
        "actual": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
            { "metadata": { "template_name": "utter_step_one" }},
            { "metadata": { "template_name": "utter_step_two" }},
        ],
        "result": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
            { "action": "utter_step_one" },
            { "action": "utter_step_two", "theme": "actual" },
        ],
    },
    {
        # bot_regression_test_data9: extra expected step
        "description": "number of steps mismatch",
        "expected": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
            { "action": "utter_step_one" },
        ],
        "actual": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
        ],
        "result": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
            { "action": "utter_step_one", "theme": "expected" },
        ],
    },
    {
        # bot_regression_test_data10: doesn't matter whether entities key is not present, or an empty list
        "expected": [
            { "user": "run step one", "intent": "step_one" },
        ],
        "actual": [
            { "user": "run step one", "intent": "step_one", "entities": [] },
        ],
        "result": [{ "user": "run step one", "intent": "step_one" }],
    },
]

@pytest.mark.parametrize("test_data", bot_regression_test_data)
def test_bot_regression_test_channel(test_data):
    input_channel = BotRegressionTestInput()
    result = input_channel.compare_step_lists(test_data.get("actual"), test_data.get("expected"))
    assert result == test_data.get("result")
