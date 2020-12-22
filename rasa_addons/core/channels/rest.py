import rasa
import os
import logging
import inspect
from rasa.core.channels.channel import UserMessage, CollectingOutputChannel, InputChannel
from rasa.core.channels.rest import RestInput
from sanic.request import Request
from sanic import Blueprint, response
from asyncio import CancelledError
from typing import Text, List, Dict, Any, Optional, Callable, Iterable, Awaitable
from sanic.response import HTTPResponse
from rasa_addons.core.channels.graphql import get_config_via_graphql

logger = logging.getLogger(__name__)


class BotfrontRestOutput(CollectingOutputChannel):
    @staticmethod
    def _message(
        recipient_id: Text,
        text: Text = None,
        image: Text = None,
        buttons: List[Dict[Text, Any]] = None,
        quick_replies: List[Dict[Text, Any]] = None,
        attachment: Text = None,
        custom: Dict[Text, Any] = None,
        metadata: Dict[Text, Any] = {},
    ) -> Dict:
        """Create a message object that will be stored."""

        obj = {
            "recipient_id": recipient_id,
            "text": text,
            "image": image,
            "quick_replies": quick_replies,
            "buttons": buttons,
            "attachment": attachment,
            "metadata": metadata,
        }

        if custom: obj.update(custom)

        # filter out any values that are `None`
        return {k: v for k, v in obj.items() if v is not None}

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        message_parts = text.split("\n\n")
        for message_part in message_parts:
            await self._persist_message(
                self._message(
                    recipient_id, text=message_part, metadata=kwargs.get("metadata", {})
                )
            )

    async def send_image_url(
        self, recipient_id: Text, image: Text, **kwargs: Any
    ) -> None:
        """Sends an image. Default will just post the url as a string."""

        await self._persist_message(
            self._message(
                recipient_id, image=image, metadata=kwargs.get("metadata", {})
            )
        )

    async def send_attachment(
        self, recipient_id: Text, attachment: Text, **kwargs: Any
    ) -> None:
        """Sends an attachment. Default will just post as a string."""

        await self._persist_message(
            self._message(
                recipient_id, attachment=attachment, metadata=kwargs.get("metadata", {})
            )
        )

    async def send_text_with_buttons(
        self,
        recipient_id: Text,
        text: Text,
        buttons: List[Dict[Text, Any]],
        **kwargs: Any,
    ) -> None:
        await self._persist_message(
            self._message(
                recipient_id,
                text=text,
                buttons=buttons,
                metadata=kwargs.get("metadata", {}),
            )
        )

    async def send_quick_replies(
        self,
        recipient_id: Text,
        text: Text,
        quick_replies: List[Dict[Text, Any]],
        **kwargs: Any,
    ) -> None:
        await self._persist_message(
            self._message(
                recipient_id,
                text=text,
                quick_replies=quick_replies,
                metadata=kwargs.get("metadata", {}),
            )
        )

    async def send_custom_json(
        self, recipient_id: Text, json_message: Dict[Text, Any], **kwargs: Any
    ) -> None:
        await self._persist_message(
            self._message(
                recipient_id, custom=json_message, metadata=kwargs.get("metadata", {})
            )
        )

    async def send_elements(
        self, recipient_id: Text, elements: Iterable[Dict[Text, Any]], **kwargs: Any
    ) -> None:
        attachment = {
            "type": "template",
            "payload": {"template_type": "generic", "elements": elements},
        }
        await self._persist_message(
            self._message(
                recipient_id,
                attachment=attachment,
                metadata=kwargs.get("metadata", {}),
            )
        )


class BotfrontRestInput(RestInput):
    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        credentials = credentials or {}
        return cls(credentials.get("config"))

    def __init__(self, config: Optional[Dict[Text, Any]] = None):
        self.config = config

    def get_metadata(self, request: Request) -> Optional[Dict[Text, Any]]:
        return request.json.get("customData", {})

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[None]]
    ) -> Blueprint:
        custom_webhook = Blueprint(
            "custom_webhook_{}".format(type(self).__name__),
            inspect.getmodule(self).__name__,
        )

        # noinspection PyUnusedLocal
        @custom_webhook.route("/", methods=["GET"])
        async def health(request: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @custom_webhook.route("/props", methods=["GET"])
        async def serve_rules(request: Request) -> HTTPResponse:
            if self.config:
                return response.json(self.config)
            else:
                props = {}
                config = await get_config_via_graphql(
                    os.environ.get("BF_URL"), os.environ.get("BF_PROJECT_ID")
                )
                if config and "credentials" in config:
                    credentials = config.get("credentials", {})
                    channel = credentials.get("rasa_addons.core.channels.rest_plus.BotfrontRestPlusInput")
                    if channel is None: channel = credentials.get("rasa_addons.core.channels.BotfrontRestPlusInput")
                    if channel is None: channel = credentials.get("rasa_addons.core.channels.rest.BotfrontRestInput")
                    if channel is None: channel = credentials.get("rasa_addons.core.channels.BotfrontRestInput", {})
                    props = channel.get("props", {})
                return response.json(props)

        @custom_webhook.route("/webhook", methods=["POST"])
        async def receive(request: Request) -> HTTPResponse:
            sender_id = await self._extract_sender(request)
            text = self._extract_message(request)
            should_use_stream = rasa.utils.endpoints.bool_arg(
                request, "stream", default=False
            )
            input_channel = self._extract_input_channel(request)
            metadata = self.get_metadata(request)

            if should_use_stream:
                return response.stream(
                    self.stream_response(
                        on_new_message, text, sender_id, input_channel, metadata
                    ),
                    content_type="text/event-stream",
                )
            else:
                collector = BotfrontRestOutput()
                # noinspection PyBroadException
                try:
                    await on_new_message(
                        UserMessage(
                            text,
                            collector,
                            sender_id,
                            input_channel=input_channel,
                            metadata=metadata,
                        )
                    )
                except CancelledError:
                    logger.error(
                        "Message handling timed out for "
                        "user message '{}'.".format(text)
                    )
                except Exception:
                    logger.exception(
                        "An exception occured while handling "
                        "user message '{}'.".format(text)
                    )
                return response.json(collector.messages)

        return custom_webhook
