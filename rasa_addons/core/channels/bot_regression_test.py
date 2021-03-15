import rasa
import logging
import inspect
from rasa.core.channels.channel import (
    UserMessage,
    InputChannel,
)
from rasa.core.channels.rest import RestInput
from sanic.request import Request
from sanic import Blueprint, response
from asyncio import CancelledError
from typing import Text, List, Dict, Any, Optional, Callable, Awaitable
from sanic.response import HTTPResponse
from rasa_addons.core.channels.rest import BotfrontRestOutput
from datetime import datetime

logger = logging.getLogger(__name__)


class BotRegressionTestOutput(BotfrontRestOutput):
    def name(self) -> Text:
        return "bot_regression_test_output"

    def send_parsed_message(self, message: UserMessage,) -> None:
        formatted_message = {
            "user": message.text,
            "intent": message.intent.get("name"),
            "entities": [
                {k: e.get(k) for k in ["entity", "start", "end", "value"]}
                for e in message.entities
            ],
        }
        self.messages.append(formatted_message)


class BotRegressionTestInput(RestInput):
    def name(self) -> Text:
        return "bot_regression_test"

    async def simulate_messages(
        self,
        steps: List[Dict[Text, Any]],
        language: Text,
        on_new_message: Callable[[UserMessage], Awaitable[None]],
    ) -> List[Dict[Text, Any]]:
        sender_id = "bot_regression_test_{:%Y-%m-%d_%H:%M:%S}".format(datetime.now())
        collector = BotRegressionTestOutput()
        for step in steps:
            if "user" in step:
                text = step.get("user")
                metadata = {"language": language}
                try:
                    await on_new_message(
                        UserMessage(
                            text,
                            collector,
                            sender_id,
                            input_channel=self.name(),
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
        return collector

    def compare_steps(self, actual_step, expected_step) -> bool:
        actual_entities = actual_step.pop("entities", [])
        expected_entities = expected_step.pop("entities", [])
        return (
            actual_step == expected_step
            and all(e in actual_entities for e in expected_entities)
            and all(e in expected_entities for e in actual_entities)
        )

    @staticmethod
    def format_as_step(step: Dict[Text, Any]) -> Dict[Text, Any]:
        if "metadata" in step and "template_name" in step.get("metadata"):
            return {"action": step.get("metadata").get("template_name")}
        else:
            return step

    def get_index_of_step(
        self, step: Dict[Text, Any], step_list: List[Dict[Text, Any]],
    ) -> int:
        return next(
            (
                i
                for i, current_step in enumerate(step_list)
                if self.compare_steps(step.copy(), current_step.copy())
            ),
            None,
        )

    @staticmethod
    def accumulate_actual_step(
        step: Dict[Text, Any], results_acc: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        step_to_append = step.copy()
        step_to_append["theme"] = "actual"
        results_acc.get("actual").append(step_to_append)

    @staticmethod
    def accumulate_matching_step(
        step: Dict[Text, Any], results_acc: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        results_acc.get("steps").extend(results_acc.get("expected"))
        results_acc["expected"] = []
        results_acc.get("steps").append(step)

    @staticmethod
    def accumulate_expected_steps(
        expected_steps: List[Dict[Text, Any]],
        stop_index: int,
        results_acc: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        results_acc.get("steps").extend(results_acc.get("actual"))
        results_acc["actual"] = []
        for _ in range(0, stop_index):
            step_to_append = expected_steps.pop(0).copy()
            step_to_append["theme"] = "expected"
            results_acc.get("steps").append(step_to_append)

    def compare_step_lists(self, actual_steps, expected_steps) -> List[Dict[Text, Any]]:
        expected_steps_remaining = expected_steps.copy()
        results_acc = {
            "expected": [],
            "actual": [],
            "steps": [],
        }
        for unformatted_actual_step in actual_steps:
            actual_step = self.format_as_step(unformatted_actual_step)
            match_index = self.get_index_of_step(actual_step, expected_steps_remaining)
            if match_index is None:
                self.accumulate_actual_step(actual_step, results_acc)
            elif match_index in range(0, len(expected_steps_remaining)):
                if match_index > 0:
                    self.accumulate_expected_steps(
                        expected_steps_remaining, match_index, results_acc
                    )
                matched_step = expected_steps_remaining.pop(0)
                self.accumulate_matching_step(matched_step, results_acc)
        # accumulate expected steps will add any leftover expected/actual steps to results_acc.steps
        self.accumulate_expected_steps(
            expected_steps_remaining, len(expected_steps_remaining), results_acc
        )
        return results_acc.get("steps")

    @staticmethod
    def check_success(steps: List[Dict[Text, Any]]) -> bool:
        return next((False for step in steps if "theme" in step), True)

    async def run_tests(
        self,
        test_cases: List[Dict[Text, Any]],
        project_id: Text,
        on_new_message: Callable[[UserMessage], Awaitable[None]],
    ) -> List[Dict[Text, Any]]:
        all_results = []
        for test_case in test_cases:
            collector = await self.simulate_messages(
                test_case.get("steps"), test_case.get("language"), on_new_message
            )
            test_results = self.compare_step_lists(
                collector.messages, test_case.get("steps")
            )
            all_results.append(
                {
                    "_id": test_case.get("_id"),
                    "testResults": test_results,
                    "success": self.check_success(test_results),
                    "projectId": project_id,
                }
            )
        return all_results

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

        @custom_webhook.route("/run", methods=["POST"])
        async def receive(request: Request) -> HTTPResponse:
            test_cases = request.json.get("test_cases")
            project_id = request.json.get("project_id")
            results = await self.run_tests(test_cases, project_id, on_new_message)
            return response.json(results)

        return custom_webhook
