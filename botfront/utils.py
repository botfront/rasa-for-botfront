import os
import yaml
import logging
import requests
import asyncio
import time
import tempfile
from rasa.utils.common import set_log_level
from asyncio import CancelledError
from typing import Text, Dict, Union
from rasa.core.events import UserUttered, BotUttered, SlotSet

logger = logging.getLogger(__name__)

from rasa.core.constants import DEFAULT_REQUEST_TIMEOUT

CONFIG_QUERY = """
query($projectId: String!) {
	getConfig(projectId: $projectId) {
        credentials
        endpoints
    }
}
"""


def auto_retry(function):
    async def auto_retried():
        tries = 1
        resp = None
        while not resp:
            if tries != 1:
                time.sleep(10)
            logger.debug(f"Trying to fetch config from server (retry #{str(tries)})")
            resp = await function()
            tries += 1
        return resp

    return auto_retried


async def get_config_via_graphql(bf_url, project_id):
    from sgqlc.endpoint.http import HTTPEndpoint
    import urllib.error

    endpoint = HTTPEndpoint(bf_url)

    @auto_retry
    async def load():
        try:
            return endpoint(CONFIG_QUERY, {"projectId": project_id})
        except urllib.error.URLError:
            return None

    data = await load()
    return data["data"]["getConfig"]


async def get_config_via_legacy_route(bf_url, project_id):
    from rasa.utils.endpoints import EndpointConfig
    import aiohttp

    response = {}
    base_url = f"{bf_url}/project/{project_id}"
    for endpoint in ["credentials", "endpoints"]:
        server = EndpointConfig(url=f"{base_url}/{endpoint}")
        async with server.session() as session:
            params = server.combine_parameters()
            url = server.url

            @auto_retry
            async def load():
                try:
                    return await session.request(
                        "GET", url, timeout=DEFAULT_REQUEST_TIMEOUT, params=params
                    )
                except aiohttp.ClientError:
                    return None

            data = await load()
            response[endpoint] = await data.json()
    return response


def set_endpoints_credentials_args_from_remote(args):
    bf_url = os.environ.get("BF_URL")
    project_id = os.environ.get("BF_PROJECT_ID")
    if not project_id or not bf_url:
        return
    if args.endpoints and args.credentials:
        return

    query_function = (
        get_config_via_graphql if "graphql" in bf_url else get_config_via_legacy_route
    )

    config = asyncio.get_event_loop().run_until_complete(
        query_function(bf_url, project_id)
    )

    if not args.endpoints:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as yamlfile:
            yaml.dump(config["endpoints"], yamlfile)
            args.endpoints = yamlfile.name
    if not args.credentials:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as yamlfile:
            yaml.dump(config["credentials"], yamlfile)
            args.credentials = yamlfile.name
