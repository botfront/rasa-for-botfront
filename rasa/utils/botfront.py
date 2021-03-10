import os
import rasa
import logging
import asyncio
import time
import tempfile
from rasa.telemetry import TELEMETRY_ENABLED_ENVIRONMENT_VARIABLE

logger = logging.getLogger(__name__)

from rasa.core.constants import DEFAULT_REQUEST_TIMEOUT

# hard code false here, since a number of things must be done to
# add support with BF
os.environ[TELEMETRY_ENABLED_ENVIRONMENT_VARIABLE] = "false"

CONFIG_QUERY = """
query($projectId: String!, $environment: String) {
	getConfig(projectId: $projectId, environment:$environment) {
        credentials
        endpoints
    }
}
"""


def auto_retry(function):
    bf_url = os.environ.get("BF_URL", "server")

    async def auto_retried():
        tries = 1
        resp = None
        while not resp:
            if tries != 1:
                time.sleep(0.5)
            logger.debug(f"Trying to fetch config from {bf_url} (retry #{str(tries)})")
            resp = await function()
            tries += 1
        return resp

    return auto_retried


async def get_config_via_graphql(bf_url, project_id):
    from sgqlc.endpoint.http import HTTPEndpoint

    logging.getLogger("sgqlc.endpoint.http").setLevel(logging.WARNING)
    import urllib.error

    environment = os.environ.get("BOTFRONT_ENV", "development")
    api_key = os.environ.get("API_KEY")
    headers = [{"Authorization": api_key}] if api_key else []
    endpoint = HTTPEndpoint(bf_url, *headers)

    @auto_retry
    async def load():
        try:
            response = endpoint(
                CONFIG_QUERY, {"projectId": project_id, "environment": environment}
            )
            if response.get("errors"):
                raise urllib.error.URLError(
                    ", ".join([e.get("message") for e in response.get("errors")])
                )
            return endpoint(
                CONFIG_QUERY, {"projectId": project_id, "environment": environment}
            )["data"]
        except urllib.error.URLError as e:
            logger.debug(e.reason)
            return None

    data = await load()
    return data["getConfig"]


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
    here = os.listdir(os.getcwd())
    if "endpoints.yml" in here and not args.endpoints:
        args.endpoints = "endpoints.yml"
    if "credentials.yml" in here and not args.credentials:
        args.credentials = "credentials.yml"
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
            rasa.shared.utils.io.write_yaml(config["endpoints"], yamlfile.name)
            args.endpoints = yamlfile.name
    if not args.credentials:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as yamlfile:
            rasa.shared.utils.io.write_yaml(config["credentials"], yamlfile.name)
            args.credentials = yamlfile.name
