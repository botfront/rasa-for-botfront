import pytest
from typing import Callable
from typing import Text, List
from rasa.core.policies import Policy

DEFAULT_BF_CONFIG_DATA = ["data/botfront/config-en.yml", "data/botfront/config-fr.yml"] # bf
DEFAULT_BF_NLU_DATA = "data/botfront/nlu" # bf

@pytest.fixture(scope="session")
def default_stack_config():
    return DEFAULT_BF_CONFIG_DATA # DEFAULT_STACK_CONFIG


@pytest.fixture(scope="session")
def default_nlu_data():
    return DEFAULT_BF_NLU_DATA # DEFAULT_NLU_DATA

@pytest.fixture(scope="session")
async def trained_rasa_model(
    trained_async: Callable,
    default_domain_path: Text,
    default_nlu_data: Text,
    default_stories_file: Text,
) -> Text:
    trained_stack_model_path = await trained_async(
        domain=default_domain_path,
        config=DEFAULT_BF_CONFIG_DATA,
        training_files=[default_nlu_data, default_stories_file],
    )

    return trained_stack_model_path


@pytest.fixture(scope="session")
async def trained_core_model(
    trained_async: Callable,
    default_domain_path: Text,
    default_nlu_data: Text,
    default_stories_file: Text,
) -> Text:
    trained_core_model_path = await trained_async(
        domain=default_domain_path,
        config=DEFAULT_BF_CONFIG_DATA,
        training_files=[default_stories_file],
    )

    return trained_core_model_path


@pytest.fixture(scope="session")
async def trained_nlu_model(
    trained_async: Callable,
    default_domain_path: Text,
    default_config: List[Policy],
    default_nlu_data: Text,
    default_stories_file: Text,
) -> Text:
    trained_nlu_model_path = await trained_async(
        domain=default_domain_path,
        config=DEFAULT_BF_CONFIG_DATA,
        training_files=[default_nlu_data],
    )

    return trained_nlu_model_path