import logging
import json
import time
import asyncio
import os
import copy
from typing import Any, List, Text, Dict, Optional
from rasa.core.events import SlotSet

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
        responder using the HANGUP_WORD, the policy goes back to its pre-
        activation behavior.

        Requires setting BF_PORTAL_URL and RASA_URL.
    """

    defaults = {
        "service": "slack",
        "triggers": ["handoff"],
        "token": None,
        "room_prefix": "support_",
        "timeout": 60 * 2,  # seconds before hanging up
        "hangup_word": "**hangup",
        "first_responders": [],
        "announcement_room": None,
    }

    def __init__(self, priority: int = 10, **kwargs: Any) -> None:
        super(BotfrontHandoffPolicy, self).__init__(priority=priority)
        if os.environ.get("BF_PORTAL_URL") is None:
            raise Exception(
                "Variable BF_PORTAL_URL not set, cannot use BotfrontHandoffPolicy."
            )
        self.endpoint = EndpointConfig(url=os.environ.get("BF_PORTAL_URL"))
        self._load_params(**kwargs)

    def get_params(self) -> Dict[Text, Any]:
        return {
            "service": self.service,
            "token": self.token,
            "room_prefix": self.room_prefix,
            "hangup_word": self.hangup_word,
            "first_responders": self.first_responders,
            "announcement_room": self.announcement_room,
            "rasa_url": os.environ.get("RASA_URL"),
        }

    def _load_params(self, **kwargs: Dict[Text, Any]) -> None:
        config = copy.deepcopy(self.defaults)
        config.update(kwargs)
        service = config.pop("service", None)
        token = config.pop("token", None)
        triggers = config.pop("triggers", [])
        room_prefix = config.pop("room_prefix", None)
        hangup_word = config.pop("hangup_word", None)
        first_responders = config.pop("first_responders", [])
        announcement_room = config.pop("announcement_room", None)
        try:
            self.timeout = float(config.pop("timeout", 0))
        except ValueError:
            raise Exception("Timeout must be a numerical value.")
        if service not in SUPPORTED_SERVICES:
            raise Exception("Handoff service not supported.")
        if token is None:
            raise Exception("Token not supplied.")
        if not isinstance(room_prefix, str):
            raise Exception("Channel prefix must be a string.")
        if not isinstance(hangup_word, str):
            raise Exception("Hangup word must be a string.")
        if not isinstance(triggers, list) or any(
            not isinstance(t, str) for t in triggers
        ):
            raise Exception("Invalid list of triggers.")
        if not isinstance(first_responders, list) or any(
            not isinstance(t, str) for t in first_responders
        ):
            raise Exception("Invalid list of first responders.")
        self.service = service
        self.token = token
        self.triggers = triggers
        self.room_prefix = room_prefix
        self.hangup_word = hangup_word
        self.first_responders = first_responders
        self.active_handoffs = {}
        self.announcement_room = announcement_room

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
            subpath=f"/handoff/{os.environ.get('BF_PROJECT_ID')}/{route}",
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

        handoff = tracker.get_slot("handoff_info") or {}
        handoff_active = handoff.get("active", False)

        if (
            handoff_active is True
            and time.time() - float(handoff.get("latest_event", time.time()))
            > self.timeout
        ):
            # no incidence on prediction, just update slot and call deactivation route
            logger.debug("Deactivating BotfrontHandoffPolicy")
            asyncio.get_running_loop().create_task(
                self._call_portal("deactivate", {"handoff": handoff})
            )

        elif handoff_active is False and intent in self.triggers:
            events = []
            for e in reversed(tracker.events):
                event = e.as_dict()
                if event.get("event") not in ["user", "bot"]:
                    continue
                if event.get("metadata", {}).get("from_handoff") is True or event.get(
                    "timestamp", 0
                ) < float(handoff.get("latest_event", 0)):
                    break
                events += [event]
            events.reverse()
            logger.debug("Activating BotfrontHandoffPolicy.")
            asyncio.get_running_loop().create_task(
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
            prediction[domain.index_for_action(ACTION_LISTEN_NAME)] = 1

        elif handoff_active is True:
            logger.debug("Listening while BotfrontHandoffPolicy is activated.")
            asyncio.get_running_loop().create_task(
                self._call_portal("post", {"handoff": handoff, "message": message,})
            )
            prediction[domain.index_for_action(ACTION_LISTEN_NAME)] = 1

        return prediction

    def persist(self, path: Text) -> None:
        config_file = os.path.join(path, "botfront_handoff_policy.json")
        meta = {
            "service": self.service,
            "token": self.token,
            "triggers": self.triggers,
            "room_prefix": self.room_prefix,
            "hangup_word": self.hangup_word,
            "first_responders": self.first_responders,
            "announcement_room": self.announcement_room,
        }
        rasa.utils.io.create_directory_for_file(config_file)
        rasa.utils.io.dump_obj_as_json_to_file(config_file, meta)

    @classmethod
    def load(cls, path: Text) -> "BotfrontHandoffPolicy":
        meta = {}
        if os.path.exists(path):
            meta_path = os.path.join(path, "botfront_handoff_policy.json")
            if os.path.isfile(meta_path):
                meta = json.loads(rasa.utils.io.read_file(meta_path))

        return cls(**meta)
