import logging
import json
import time
import asyncio
import os
import copy
from typing import Any, List, Text, Dict
from rasa.core.events import UserUttered, UserUtteranceReverted

import rasa.utils.io

from rasa.core.actions.action import ACTION_LISTEN_NAME
from rasa.core.domain import Domain
from rasa.core.policies.policy import Policy
from rasa.core.trackers import DialogueStateTracker
from rasa.utils.endpoints import EndpointConfig

logger = logging.getLogger(__name__)

SUPPORTED_SERVICES = ["slack"]


class BotfrontHandoffPolicy(Policy):
    """
        This high-priority policy checks if a user message intent is
        a defined TRIGGER. If it is, it activates a handoff, during which:
        1) all user messages are forwarded to a SERVICE, 2) predictions are
        restricted to ACTION_LISTEN and 3) all messages on the SERVICE are
        inserted back into the tracker and fed back into the output channel.
        
        Once the handoff times out or is explictly terminated by a first
        responder using the hang up command, the policy goes back to its pre-
        activation behavior.

        Requires setting BF_PORTAL_URL and RASA_URL.
    """

    defaults = {
        "service": "slack",
        "realm": None,
        "room_prefix": "support_",
        "triggers": ["botfront_handoff"],
        "on_unanswered_handoff_deactivation": None,
        "on_answered_handoff_deactivation": None,
        "on_explicit_handoff_deactivation": None,
        "first_responders": [],
        "announcement_room": None,
        "timeout": 60 * 2,  # seconds before hanging up
        "timeout_unanswered": 60,  # seconds before hanging up w/o first contact
    }

    def __init__(self, priority: int = 10, **kwargs: Any) -> None:
        super(BotfrontHandoffPolicy, self).__init__(priority=priority)
        if os.environ.get("BF_PORTAL_URL") is None:
            raise Exception(
                "Variable BF_PORTAL_URL not set, cannot use BotfrontHandoffPolicy."
            )
        self.endpoint = EndpointConfig(url=os.environ.get("BF_PORTAL_URL"))
        self._load_params(**kwargs)

    def _print_auth_link(self, response):
        auth_link = response.get("auth_link")
        if auth_link:
            logger.error(auth_link)

    def get_params(self) -> Dict[Text, Any]:
        return {
            "service": self.service,
            "realm": self.realm,
            "room_prefix": self.room_prefix,
            "triggers": self.triggers,
            "on_unanswered_handoff_deactivation": self.on_unanswered_handoff_deactivation,
            "on_answered_handoff_deactivation": self.on_answered_handoff_deactivation,
            "on_explicit_handoff_deactivation": self.on_explicit_handoff_deactivation,
            "first_responders": self.first_responders,
            "announcement_room": self.announcement_room,
            "timeout": self.timeout,
            "timeout_unanswered": self.timeout_unanswered,
            "rasa_url": os.environ.get("RASA_URL"),
            "project_id": os.environ.get("BF_PROJECT_ID"),
        }

    def _load_params(self, **kwargs: Dict[Text, Any]) -> None:
        config = copy.deepcopy(self.defaults)
        config.update(kwargs)
        service = config.get("service")
        realm = config.get("realm")
        room_prefix = config.get("room_prefix")
        triggers = config.get("triggers")
        first_responders = config.get("first_responders")
        announcement_room = config.get("announcement_room")
        try:
            self.timeout = float(config.pop("timeout", None))
            self.timeout_unanswered = float(config.pop("timeout_unanswered", None))
        except (ValueError, TypeError):
            raise Exception("Timeouts must be numerical values.")
        if service not in SUPPORTED_SERVICES:
            raise Exception("Handoff service not supported.")
        if realm is None:
            raise Exception("Realm not supplied.")
        if not isinstance(room_prefix, str):
            raise Exception("Channel prefix must be a string.")
        if not isinstance(triggers, list) or any(
            not isinstance(t, str) for t in triggers
        ):
            raise Exception("Invalid list of triggers.")
        if not isinstance(first_responders, list) or any(
            not isinstance(t, str) for t in first_responders
        ):
            raise Exception("Invalid list of first responders.")
        self.service = service
        self.realm = realm
        self.room_prefix = room_prefix
        self.triggers = triggers
        self.on_unanswered_handoff_deactivation = config.get(
            "on_unanswered_handoff_deactivation"
        )
        self.on_answered_handoff_deactivation = config.get(
            "on_answered_handoff_deactivation"
        )
        self.on_explicit_handoff_deactivation = config.get(
            "on_explicit_handoff_deactivation"
        )
        self.first_responders = first_responders
        self.announcement_room = announcement_room
        self.active_handoffs = {}

    def train(
        self,
        training_trackers: List[DialogueStateTracker],
        domain: Domain,
        **kwargs: Any,
    ) -> None:
        pass

    async def _call_portal(self, route, body):
        return await self.endpoint.request(
            json={"params": self.get_params(), **body},
            method="post",
            subpath=f"/handoff/{route}",
        )

    def predict_action_probabilities(
        self, tracker: DialogueStateTracker, domain: Domain
    ) -> List[float]:
        prediction = [0.0] * domain.num_actions
        intent = tracker.latest_message.intent.get("name")
        message = tracker.latest_message.text
        latest_event = tracker.latest_message.timestamp
        sender_id = tracker.sender_id
        user_id = (tracker.latest_message.metadata or {}).get("userId")

        handoff = tracker.get_slot("botfront_handoff_info") or {}
        handoff_active = handoff.get("active", False)

        rewind_occured_before_user_spoke = False
        for e in reversed(tracker.events):
            if isinstance(e, UserUtteranceReverted):
                rewind_occured_before_user_spoke = True
                break
            if isinstance(e, UserUttered):
                break
        if rewind_occured_before_user_spoke:
            return prediction  # don't activate as a result of a rewind

        if handoff_active is True and time.time() - float(
            handoff.get("latest_event", time.time())
        ) > (
            self.timeout
            if handoff.get("agent_answered", False)
            else self.timeout_unanswered
        ):
            # no incidence on prediction, just update slot and call deactivation route
            logger.debug("Deactivating BotfrontHandoffPolicy")
            asyncio.get_running_loop().create_task(
                self._call_portal("deactivate", {"handoff": handoff})
            )
            prediction[domain.index_for_action(ACTION_LISTEN_NAME)] = 1

        elif handoff_active is False and intent in self.triggers:
            events = []
            for e in reversed(tracker.events):
                event = e.as_dict()
                if (
                    event.get("event") == "slot"
                    and event.get("name") == "botfront_handoff_info"
                    and event.get("value", {}).get("active") is False
                ):
                    break
                if event.get("event") not in ["user", "bot"]:
                    continue
                if event.get("metadata", {}).get("from_handoff") is True or event.get(
                    "timestamp", 0
                ) < float(handoff.get("latest_event", 0)):
                    break
                events += [event]
            events.reverse()
            logger.debug("Activating BotfrontHandoffPolicy.")
            task = asyncio.get_running_loop().create_task(
                self._call_portal(
                    "activate",
                    {
                        "events": events,
                        "latest_event": latest_event,
                        "sender_id": sender_id,
                        "user_id": user_id,
                    },
                )
            )
            task.add_done_callback(lambda r: self._print_auth_link(r.result()))
            prediction[domain.index_for_action(ACTION_LISTEN_NAME)] = 1

        elif handoff_active is True:
            logger.debug("Listening while BotfrontHandoffPolicy is activated.")
            task = asyncio.get_running_loop().create_task(
                self._call_portal("post", {"handoff": handoff, "message": message,})
            )
            prediction[domain.index_for_action(ACTION_LISTEN_NAME)] = 1

        return prediction

    def persist(self, path: Text) -> None:
        config_file = os.path.join(path, "botfront_handoff_policy.json")
        rasa.utils.io.create_directory_for_file(config_file)
        rasa.utils.io.dump_obj_as_json_to_file(config_file, self.get_params())

    @classmethod
    def load(cls, path: Text) -> "BotfrontHandoffPolicy":
        meta = {}
        if os.path.exists(path):
            meta_path = os.path.join(path, "botfront_handoff_policy.json")
            if os.path.isfile(meta_path):
                meta = json.loads(rasa.utils.io.read_file(meta_path))

        return cls(**meta)
