import os
import yaml
import logging
import requests
import asyncio
import aiohttp
import tempfile
from rasa.utils.common import set_log_level
from asyncio import CancelledError
from rasa.utils.endpoints import EndpointConfig
from typing import Text, Dict, Union
from rasa.core.events import UserUttered, BotUttered, SlotSet
logger = logging.getLogger(__name__)

from rasa.core.constants import DEFAULT_REQUEST_TIMEOUT

async def load(session, params, url):
    try:
        return await session.request("GET", url, timeout=DEFAULT_REQUEST_TIMEOUT, params=params)
    except aiohttp.ClientError:
        return None

async def load_from_remote(
    server: EndpointConfig, name: Text, temp_file=True
) -> Union[Text, Dict]:
    """Returns and object or a file from an endpoint
    """

    logger.debug("Requesting {} from server {}...".format(name, server.url))

    async with server.session() as session:
        params = server.combine_parameters()
        url = server.url
        tries = 1; resp = None
        while not resp:
            if tries == 1 or tries % 5000 == 0:
                logger.debug('Trying to fetch {} from server (retry #{})'.format(name, str(tries)))
            resp = await load(session, params, url)
            tries += 1
        if resp.status != 200:
            raise aiohttp.ClientError('Tried to fetch {} from server, but server response '
                                        'status code is {}.'.format(name, resp.status))
        json = await resp.json()
        if temp_file is True:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as yamlfile:
                yaml.dump(json, yamlfile)
                return yamlfile.name
        else:
            return json

def set_endpoints_credentials_args_from_remote(args):
    bf_url = os.environ.get('BF_URL')
    project_id = os.environ.get('BF_PROJECT_ID')
    if not project_id or not bf_url:
        return

    if not args.endpoints:
        logger.info("Fetching endpoints from server")
        url = "{}/project/{}/{}".format(bf_url, project_id, "endpoints")
        try:
            args.endpoints = asyncio.get_event_loop().run_until_complete(
                load_from_remote(EndpointConfig(url=url), "endpoints")
            )
        except aiohttp.ClientError:
            raise aiohttp.ClientError('Could not load endpoints for project {}.'.format(project_id))

    if not args.credentials:
        logger.info("Fetching credentials from server")
        url = "{}/project/{}/{}".format(bf_url, project_id, "credentials")
        try:
            args.credentials = asyncio.get_event_loop().run_until_complete(
                load_from_remote(EndpointConfig(url=url), "credentials")
            )
        except aiohttp.ClientError:
            raise aiohttp.ClientError('Could not load credentials for project {}.'.format(project_id))


def get_latest_parse_data_language(all_events):
    events = reversed(all_events)
    try:
        while True:
            event = next(events)
            if event['event'] == 'user' and 'parse_data' in event and 'language' in event['parse_data']:
                return event['parse_data']['language']

    except StopIteration:
        return None


def get_project_default_language(project_id, base_url):
    url = '{base_url}/project/{project_id}/models/published'.format(base_url=base_url, project_id=project_id)
    result = requests.get(url)
    try:
        result = requests.get(url)
        if result.status_code == 200:
            if result.json():
                return result.json().get('default_language', None)
            else:
                return result.json().error
        else:
            logger.error(
                "Failed to get project default language"
                "Error: {}".format(result.json()))
            return None

    except Exception:
        logger.error(
            "Failed to get project default language"
            "Error: {}".format(result.json()))
        return None


def events_to_dialogue(events):
    dialogue = ""
    for e in events:
        if e["event"] == 'user':
            dialogue += "\n User: {}".format(e['text'])
        elif e["event"] == 'bot':
            dialogue += "\n Bot: {}".format(e['text'])
    return dialogue


def slots_from_profile(user_id, user_profile):
    return [SlotSet("user_id", user_id), SlotSet("first_name", user_profile["first_name"]),
            SlotSet("last_name", user_profile["last_name"]), SlotSet("phone", user_profile["phone"]),
            SlotSet('user_profile', user_profile)]
