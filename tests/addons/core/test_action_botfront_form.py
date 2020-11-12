from rasa_addons.core.actions.action_botfront_form import ActionBotfrontForm
from rasa_addons.core.nlg.bftemplate import BotfrontTemplatedNaturalLanguageGenerator
from rasa.shared.core.domain import Domain
from rasa.core.channels.channel import OutputChannel
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.events import (
    UserUtteranceReverted,
    UserUttered,
    ActionExecuted,
    Event,
    SlotSet,
    BotUttered,
)
from rasa.shared.core.slots import Slot
import pytest

nlg = BotfrontTemplatedNaturalLanguageGenerator()


def new_form_and_tracker(form_spec, requested_slot, additional_slots=[]):
    form = ActionBotfrontForm(form_spec.get("form_name"))
    tracker = DialogueStateTracker.from_dict(
        "default",
        [],
        [
            Slot(name=requested_slot),
            *[Slot(name=name) for name in additional_slots],
            Slot(name="requested_slot", initial_value=requested_slot),
        ],
    )
    form.form_spec = form_spec  # load spec manually
    return form, tracker


def required_slots_graph(conjunction="OR", negated=False):
    return {
        "nodes": [
            {"id": "0", "type": "start"},
            {"id": "1", "type": "slot", "slotName": "age"},
            {"id": "2", "type": "slot", "slotName": "authorization"},
            {"id": "3", "type": "slot", "slotName": "comments"},
        ],
        "edges": [
            {
                "id": "a",
                "type": "condition",
                "source": "0",
                "target": "1",
                "condition": None,
            },
            {
                "id": "d",
                "type": "condition",
                "source": "1",
                "target": "3",
                "condition": None,
            },
            {
                "id": "b",
                "type": "condition",
                "source": "1",
                "target": "2",
                "condition": {
                    "type": "group",
                    "id": "9a99988a-0123-4456-b89a-b1607f326fd8",
                    "children1": {
                        "a98ab9b9-cdef-4012-b456-71607f326fd9": {
                            "type": "rule",
                            "properties": {
                                "field": "age",
                                "operator": "lt",
                                "value": ["18"],
                                "valueSrc": ["value"],
                                "valueType": ["text"],
                                "valueError": [None],
                            },
                        },
                        "98a8a9ba-0123-4456-b89a-b16e721c8cd0": {
                            "type": "rule",
                            "properties": {
                                "field": "age",
                                "operator": "gt",
                                "value": ["65"],
                                "valueSrc": ["value"],
                                "valueType": ["text"],
                                "valueError": [None],
                            },
                        },
                    },
                    "properties": {"conjunction": conjunction, "not": negated},
                },
            },
            {
                "id": "c",
                "type": "condition",
                "source": "2",
                "target": "3",
                "condition": {
                    "type": "group",
                    "id": "9a99988a-0123-4456-b89a-b1607f326fd8",
                    "children1": {
                        "a98ab9b9-cdef-4012-b456-71607f326fd9": {
                            "type": "rule",
                            "properties": {
                                "field": "authorization",
                                "operator": "is_exactly",
                                "value": ["true"],
                                "valueSrc": ["value"],
                                "valueType": ["text"],
                                "valueError": [None],
                            },
                        }
                    },
                    "properties": {"conjunction": "OR", "not": None},
                },
            },
        ],
    }

def required_slots_graph_with_set_slots(conjunction="OR", negated=False):
    return {
        "nodes": [
            *(required_slots_graph(conjunction, negated).get("nodes")),
            {"id": "4", "type": "slotSet", "slotName": "finished", "slotValue": False},
            {"id": "5", "type": "slotSet", "slotName": "finished", "slotValue": True},
        ],
        "edges": [
            *(required_slots_graph(conjunction, negated).get("edges")),
            {
                "id": "e",
                "type": "condition",
                "source": "2",
                "target": "4",
                "condition": None,
            },
            {
                "id": "f",
                "type": "condition",
                "source": "3",
                "target": "5",
                "condition": None,
            },
        ],
    }


def test_extract_requested_slot_default():
    """Test default extraction of a slot value from entity with the same name
    """

    spec = {"name": "default_form"}

    form, tracker = new_form_and_tracker(spec, "some_slot")
    tracker.update(
        UserUttered(entities=[{"entity": "some_slot", "value": "some_value"}])
    )

    slot_values = form.extract_requested_slot(
        OutputChannel(), nlg, tracker, Domain.empty()
    )
    assert slot_values == {"some_slot": "some_value"}


def test_extract_requested_slot_from_entity_no_intent():
    """Test extraction of a slot value from entity with the different name
        and any intent
    """

    spec = {
        "name": "default_form",
        "slots": [
            {
                "name": "some_slot",
                "filling": [{"type": "from_entity", "entity": ["some_entity"]}],
            }
        ],
    }

    form, tracker = new_form_and_tracker(spec, "some_slot")
    tracker.update(
        UserUttered(entities=[{"entity": "some_entity", "value": "some_value"}])
    )

    slot_values = form.extract_requested_slot(
        OutputChannel(), nlg, tracker, Domain.empty()
    )
    assert slot_values == {"some_slot": "some_value"}


def test_extract_requested_slot_from_entity_with_intent():
    """Test extraction of a slot value from entity with the different name
        and certain intent
    """

    spec = {
        "name": "default_form",
        "slots": [
            {
                "name": "some_slot",
                "filling": [
                    {
                        "type": "from_entity",
                        "entity": ["some_entity"],
                        "intent": ["some_intent"],
                    }
                ],
            }
        ],
    }

    form, tracker = new_form_and_tracker(spec, "some_slot")
    tracker.update(
        UserUttered(
            intent={"name": "some_intent", "confidence": 1.0},
            entities=[{"entity": "some_entity", "value": "some_value"}],
        )
    )

    slot_values = form.extract_requested_slot(
        OutputChannel(), nlg, tracker, Domain.empty()
    )
    assert slot_values == {"some_slot": "some_value"}

    tracker.update(
        UserUttered(
            intent={"name": "some_other_intent", "confidence": 1.0},
            entities=[{"entity": "some_entity", "value": "some_value"}],
        )
    )

    slot_values = form.extract_requested_slot(
        OutputChannel(), nlg, tracker, Domain.empty()
    )
    assert slot_values == {}


def test_extract_requested_slot_from_intent():
    """Test extraction of a slot value from certain intent
    """

    spec = {
        "name": "default_form",
        "slots": [
            {
                "name": "some_slot",
                "filling": [
                    {
                        "type": "from_intent",
                        "intent": ["some_intent"],
                        "value": "some_value",
                    }
                ],
            }
        ],
    }

    form, tracker = new_form_and_tracker(spec, "some_slot")
    tracker.update(UserUttered(intent={"name": "some_intent", "confidence": 1.0}))

    slot_values = form.extract_requested_slot(
        OutputChannel(), nlg, tracker, Domain.empty()
    )
    assert slot_values == {"some_slot": "some_value"}

    tracker.update(UserUttered(intent={"name": "some_other_intent", "confidence": 1.0}))

    slot_values = form.extract_requested_slot(
        OutputChannel(), nlg, tracker, Domain.empty()
    )
    assert slot_values == {}


def test_extract_requested_slot_from_text_with_not_intent():
    """Test extraction of a slot value from text with certain intent
    """

    spec = {
        "name": "default_form",
        "slots": [
            {
                "name": "some_slot",
                "filling": [{"type": "from_text", "not_intent": ["some_intent"],}],
            }
        ],
    }

    form, tracker = new_form_and_tracker(spec, "some_slot")
    tracker.update(
        UserUttered(intent={"name": "some_intent", "confidence": 1.0}, text="some_text")
    )

    slot_values = form.extract_requested_slot(
        OutputChannel(), nlg, tracker, Domain.empty()
    )
    assert slot_values == {}

    tracker.update(
        UserUttered(
            intent={"name": "some_other_intent", "confidence": 1.0}, text="some_text"
        )
    )

    slot_values = form.extract_requested_slot(
        OutputChannel(), nlg, tracker, Domain.empty()
    )
    assert slot_values == {"some_slot": "some_text"}

@pytest.mark.parametrize(
    "operator, value, comparatum, result",
    [
        ("is_in", "hey", ["hey", "ho", "fee"], True),
        ("is_exactly", "aheya", "hey", False),
        ("contains", "aheya", "hey", True),
        ("ends_with", "hey", 5, None),
        ("eq", "5", 5, True),
        ("eq", "5", "a", None),
        ("gt", 4, 5, False),
        ("shorter_or_equal", "hey", "3", True),
        ("shorter_or_equal", "heya", "3", False),
        ("shorter_or_equal", "heya", "a", None),
        ("email", "joe@hotmail.com", None, True),
        ("email", "joe@ hotmail.com", None, False),
        ("word", "joe is", None, False),
        ("word", "joe", None, True),
    ],
)
async def test_validation(value, operator, comparatum, result, caplog):
    spec = {
        "name": "default_form",
        "slots": [
            {
                "name": "some_slot",
                "validation": {"operator": operator, "comparatum": comparatum,},
            }
        ],
    }

    form, tracker = new_form_and_tracker(spec, "some_slot")
    tracker.update(UserUttered(entities=[{"entity": "some_slot", "value": value}]))

    events = await form.validate(OutputChannel(), nlg, tracker, Domain.empty())

    if result is True:
        assert len(events) == 1
        assert isinstance(events[0], SlotSet) and events[0].value == value
    else:
        assert len(events) == 2
        assert isinstance(events[0], SlotSet) and events[0].value == None
        assert (
            isinstance(events[1], BotUttered)
            and events[1].text == "utter_invalid_some_slot"
        )
        if result is None:
            assert f"Validation operator '{operator}' requires" in caplog.messages[0]


@pytest.mark.parametrize(
    "graph, age, authorization_req, with_slots",
    [
        # under 18 or over 65
        (required_slots_graph("OR", False), 17, True, False),
        (required_slots_graph("OR", False), 30, False, False),
        (required_slots_graph("OR", False), 66, True, False),
        # at least 18 and at most 65
        (required_slots_graph("OR", True), 17, False, False),
        (required_slots_graph("OR", True), 30, True, False),
        (required_slots_graph("OR", True), 66, False, False),
        # under 18 and over 65 (contradiction)
        (required_slots_graph("AND", False), 17, False, False),
        (required_slots_graph("AND", False), 30, False, False),
        (required_slots_graph("AND", False), 66, False, False),
        # at least 18 or at most 65 (tautology)
        (required_slots_graph("AND", True), 17, True, False),
        (required_slots_graph("AND", True), 30, True, False),
        (required_slots_graph("AND", True), 66, True, False),

        (required_slots_graph_with_set_slots("OR", False), 17, True, True),
        (required_slots_graph_with_set_slots("OR", False), 30, False, True),
        (required_slots_graph_with_set_slots("OR", False), 66, True, True),
        # at least 18 and at most 65
        (required_slots_graph_with_set_slots("OR", True), 17, False, True),
        (required_slots_graph_with_set_slots("OR", True), 30, True, True),
        (required_slots_graph_with_set_slots("OR", True), 66, False, True),
        # under 18 and over 65 (contradiction)
        (required_slots_graph_with_set_slots("AND", False), 17, False, True),
        (required_slots_graph_with_set_slots("AND", False), 30, False, True),
        (required_slots_graph_with_set_slots("AND", False), 66, False, True),
        # at least 18 or at most 65 (tautology)
        (required_slots_graph_with_set_slots("AND", True), 17, True, True),
        (required_slots_graph_with_set_slots("AND", True), 30, True, True),
        (required_slots_graph_with_set_slots("AND", True), 66, True, True),
    ],
)
async def test_required_slots_with_set_slots(graph, age, authorization_req, with_slots):
    """
        (start)
        |
        AGE --- fail age condition --- AUTHORIZATION --- fail authorization
        |                               |                       condition
        |                               pass authorization          |
        pass age condition              condition                   |
        |                               /                           if with_slots (setSlot finished=False)
        |                              /                           
        COMMENTS ---------------------                           
        |                                                       
        if with_slots (setSlot finished=True)
    """

    spec = {"name": "default_form", "graph_elements": graph}

    form, tracker = new_form_and_tracker(
        spec, "age", ["authorization", "comments"]
    )
    tracker.update(SlotSet("age", age))

    # first test with no authorization
    tracker.update(SlotSet("authorization", "false"))

    def get_finished_set_slot(value: bool):
        return {
            "name": "finished",
            "type": "slotSet",
            "value": value,
        }

    def get_last_required_slot():
        if with_slots:
            return [get_finished_set_slot(False)] if authorization_req else [get_finished_set_slot(True)]
        else:
            return []

    assert form.required_slots(tracker) == [
        "age",
        *(["authorization"] if authorization_req else []),
        # here comments is only required if authorization is not required
        *(["comments"] if not authorization_req else []),
        *(get_last_required_slot())
    ]

    # then with authorization
    tracker.update(SlotSet("authorization", "true"))
    assert form.required_slots(tracker) == [
        "age",
        *(["authorization"] if authorization_req else []),
        # now comments is always required
        "comments",
        *([get_finished_set_slot(True)] if with_slots else [])
    ]