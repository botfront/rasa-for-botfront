botfront_test_channel_test_data = [
    {
        # full match
        "description": "actual matches expected",
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
        # intent mismatch
        "description": "intent mismatch",
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
        # entity name mismatch
        "description": "entity name mismatch",
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
        #entity value mismatch
        "description": "entity value mismatch",
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
        # entity start mismatch
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
        # entity end mismatch
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
    {
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
        # action mismatch
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
        # extra actual step
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
        # extra expected step
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
]