import os
import tempfile
import time
import shutil
from pathlib import Path
from typing import Text, Optional, Dict, Any
from unittest.mock import Mock

import pytest
from _pytest.tmpdir import TempdirFactory

import rasa
import rasa.core
import rasa.nlu
from rasa.importers.rasa import RasaFileImporter
from rasa.constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_DATA_PATH,
    DEFAULT_DOMAIN_PATH,
    DEFAULT_CORE_SUBDIRECTORY_NAME,
)
from rasa.core.domain import Domain
from rasa.core.utils import get_dict_hash
from rasa import model
from rasa.model import (
    FINGERPRINT_CONFIG_KEY,
    FINGERPRINT_DOMAIN_WITHOUT_NLG_KEY,
    FINGERPRINT_NLG_KEY,
    FINGERPRINT_FILE_PATH,
    FINGERPRINT_NLU_DATA_KEY,
    FINGERPRINT_RASA_VERSION_KEY,
    FINGERPRINT_STORIES_KEY,
    FINGERPRINT_TRAINED_AT_KEY,
    FINGERPRINT_CONFIG_CORE_KEY,
    FINGERPRINT_CONFIG_NLU_KEY,
    SECTION_CORE,
    SECTION_NLU,
    create_package_rasa,
    get_latest_model,
    get_model,
    get_model_subdirectories,
    model_fingerprint,
    Fingerprint,
    did_section_fingerprint_change,
    should_retrain,
    FingerprintComparisonResult,
)
from rasa.exceptions import ModelNotFound


def test_get_latest_model(trained_model):
    import shutil

    path_of_latest = os.path.join(os.path.dirname(trained_model), "latest.tar.gz")
    shutil.copy(trained_model, path_of_latest)

    model_directory = os.path.dirname(path_of_latest)

    assert get_latest_model(model_directory) == path_of_latest


def test_get_model_from_directory(trained_model):
    unpacked = get_model(trained_model)

    assert os.path.exists(os.path.join(unpacked, DEFAULT_CORE_SUBDIRECTORY_NAME))
    assert os.path.exists(os.path.join(unpacked, "nlu"))


def test_get_model_context_manager(trained_model):
    with get_model(trained_model) as unpacked:
        assert os.path.exists(unpacked)

    assert not os.path.exists(unpacked)


@pytest.mark.parametrize("model_path", ["foobar", "rasa", "README.md", None])
def test_get_model_exception(model_path):
    with pytest.raises(ModelNotFound):
        get_model(model_path)


def test_get_model_from_directory_with_subdirectories(
    trained_model, tmpdir_factory: TempdirFactory
):
    unpacked = get_model(trained_model)
    unpacked_core, unpacked_nlu = get_model_subdirectories(unpacked)

    assert unpacked_core
    assert unpacked_nlu

    directory = tmpdir_factory.mktemp("empty_model_dir").strpath
    with pytest.raises(ModelNotFound):
        get_model_subdirectories(directory)


def test_get_model_from_directory_nlu_only(trained_model):
    unpacked = get_model(trained_model)
    shutil.rmtree(os.path.join(unpacked, DEFAULT_CORE_SUBDIRECTORY_NAME))
    unpacked_core, unpacked_nlu = get_model_subdirectories(unpacked)

    assert not unpacked_core
    assert unpacked_nlu


def _fingerprint(
    config: Optional[Text] = None,
    config_nlu: Optional[Dict[Text, Text]] = None,
    config_core: Optional[Text] = None,
    domain: Optional[int] = None,
    nlg: Optional[Any] = None,
    stories: Optional[Any] = None,
    nlu: Optional[Any] = None,
    rasa_version: Text = "1.0",
):
    return {
        FINGERPRINT_CONFIG_KEY: config if config is not None else ["test"],
        FINGERPRINT_CONFIG_CORE_KEY: config_core
        if config_core is not None
        else ["test"],
        FINGERPRINT_CONFIG_NLU_KEY: config_nlu if config_nlu is not None else {"en": "test_en", "fr": "test_fr"},
        FINGERPRINT_DOMAIN_WITHOUT_NLG_KEY: domain if domain is not None else ["test"],
        FINGERPRINT_NLG_KEY: nlg if nlg is not None else ["test"],
        FINGERPRINT_TRAINED_AT_KEY: time.time(),
        FINGERPRINT_RASA_VERSION_KEY: rasa_version,
        FINGERPRINT_STORIES_KEY: stories if stories is not None else ["test"],
        FINGERPRINT_NLU_DATA_KEY: nlu if nlu is not None else {"en": "test_en", "fr": "test_fr"},
    }


def test_persist_and_load_fingerprint():
    from rasa.model import persist_fingerprint, fingerprint_from_path

    fingerprint = _fingerprint()
    output_directory = tempfile.mkdtemp()

    persist_fingerprint(output_directory, fingerprint)
    actual = fingerprint_from_path(output_directory)

    assert actual == fingerprint


@pytest.mark.parametrize(
    "fingerprint2, changed",
    [
        (_fingerprint(config=["other"]), True),
        (_fingerprint(config_core=["other"]), True),
        (_fingerprint(domain=["other"]), True),
        (_fingerprint(domain=Domain.empty()), True),
        (_fingerprint(stories=["test", "other"]), True),
        (_fingerprint(rasa_version="100"), True),
        (_fingerprint(config=["other"], domain=["other"]), True),
        (_fingerprint(nlg=["other"]), False),
        (_fingerprint(nlu=["test", "other"]), False),
        (_fingerprint(config_nlu=["other"]), False),
    ],
)
def test_core_fingerprint_changed(fingerprint2, changed):
    fingerprint1 = _fingerprint()
    assert (
        did_section_fingerprint_change(fingerprint1, fingerprint2, SECTION_CORE)
        is changed
    )


def test_nlu_fingerprint_not_changed():
    assert not did_section_fingerprint_change(_fingerprint(), _fingerprint(), SECTION_NLU)


@pytest.mark.parametrize(
    "fingerprint2",
    [
        _fingerprint(config=["other"]),
        _fingerprint(rasa_version="100"),
        _fingerprint(rasa_version="100", config=["other"]),
        _fingerprint(config_nlu={"en": "test_en", "fr": "test_fr_changed"}, nlu={"en": "test_en_changed", "fr": "test_fr"}),
        _fingerprint(nlu={"en": "test_en_changed", "fr": "test_fr_changed"}),
        _fingerprint(config_nlu={"en": "test_en_changed", "fr": "test_fr_changed"}),

    ],
)
def test_nlu_fingerprint_changed_all(fingerprint2):
    fingerprint1 = _fingerprint()
    assert sorted(did_section_fingerprint_change(fingerprint1, fingerprint2, SECTION_NLU)) == ["en", "fr"]


@pytest.mark.parametrize(
    "fingerprint",
    [
        {
            "new": _fingerprint(nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "old": _fingerprint(),
            "retrain_nlu": ["fr"],
        },
        {
            "new": _fingerprint(nlu={"en": "test_en_changed", "fr": "test_fr_changed"}),
            "old": _fingerprint(),
            "retrain_nlu": ["en", "fr"],
        },
        {
            "new": _fingerprint(nlu={"en": "test_en_changed", "fr": "test_fr"}),
            "old": _fingerprint(),
            "retrain_core": False,
            "retrain_nlu": ["en"],
        },
        {
            "new": _fingerprint(config_nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "old": _fingerprint(),
            "retrain_nlu": ["fr"],
        },
        {
            "new": _fingerprint(config_nlu={"en": "test_en_changed", "fr": "test_fr_changed"}),
            "old": _fingerprint(),
            "retrain_nlu": ["en", "fr"],
        },
        {
            "new": _fingerprint(config_nlu={"en": "test_en_changed", "fr": "test_fr"}),
            "old": _fingerprint(),
            "retrain_nlu": ["en"],
        },
        {
            "new": _fingerprint(),
            "old": _fingerprint(),
            "retrain_nlu": [],
        },
        {
            "new": _fingerprint(nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "old": _fingerprint(nlu={}, config_nlu={}),
            "retrain_nlu": ["en", "fr"],
        },
        {
            "new": _fingerprint(nlu={}),
            "old": _fingerprint(nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "retrain_nlu": ["en", "fr"],
        },
        {
            "old": _fingerprint(nlu={}, config_nlu={}),
            "new": _fingerprint(nlu={"en": "test_en"}, config_nlu={"en": "test_en"}),
            "retrain_nlu": ["en"],
        },
        {
            "old": _fingerprint(nlu={"en": "test_en"}, config_nlu={"en": "test_en"}),
            "new": _fingerprint(nlu={"en": "test_en", "fr": "test_fr_changed"}, config_nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "retrain_nlu": ["fr"],
        },
        {
            "new": _fingerprint(nlu={"en": "test_en_changed", "fr": "test_fr"}, config_nlu={"en": "test_en", "fr": "test_fr"}),
            "old": _fingerprint(nlu={"en": "test_en", "fr": "test_fr"}, config_nlu={"en": "test_en", "fr": "test_fr"}),
            "retrain_nlu": ["en"],
        },
        {
            "old": _fingerprint(config='', config_nlu={}, nlu={}),
            "new": _fingerprint(config='', config_nlu={'en': 'e50f96c444c3804c4bb249b8a802948b'}, nlu={'en': 'asdasdasdasd'}),
            "retrain_nlu": ["en"],
        }
        # {
        #     "old": _fingerprint(config_nlu={"en": "en"}, nlu={}),
        #     "new": _fingerprint(config_nlu={"en": "en"}, nlu={"en": "test_en"}),
        #     "retrain_core": False,
        #     "retrain_nlu": ["en"],
        # },
    ],
)
def test_nlu_fingerprint_languages_changed(fingerprint):
    assert sorted(did_section_fingerprint_change(fingerprint["old"], fingerprint["new"], SECTION_NLU)) == fingerprint["retrain_nlu"]


@pytest.mark.parametrize(
    "fingerprint2",
    [
        _fingerprint(config_nlu={"en": "test_en", "fr": "test_fr_changed"}),
        _fingerprint(nlu={"en": "test_en", "fr": "test_fr_changed"}),
    ],
)
def test_nlu_fingerprint_changed_fr(fingerprint2):
    fingerprint1 = _fingerprint()
    assert did_section_fingerprint_change(fingerprint1, fingerprint2, SECTION_NLU) == ["fr"]


def _project_files(
    project,
    config_file=DEFAULT_CONFIG_PATH,
    domain=DEFAULT_DOMAIN_PATH,
    training_files=DEFAULT_DATA_PATH,
):
    paths = {
        "config_file": config_file,
        "domain_path": domain,
        "training_data_paths": training_files,
    }

    paths = {k: v if v is None else os.path.join(project, v) for k, v in paths.items()}
    paths["training_data_paths"] = [paths["training_data_paths"]]

    return RasaFileImporter(**paths)


async def test_create_fingerprint_from_paths(project):
    project_files = _project_files(project)

    assert await model_fingerprint(project_files)


@pytest.mark.parametrize(
    "project_files", [["invalid", "invalid", "invalid"], [None, None, None]]
)
async def test_create_fingerprint_from_invalid_paths(project, project_files):
    from rasa.nlu.training_data import TrainingData
    from rasa.core.training.structures import StoryGraph

    project_files = _project_files(project, *project_files)
    expected = _fingerprint(
        config="",
        config_nlu="",
        config_core="",
        domain=hash(Domain.empty()),
        nlg=get_dict_hash(Domain.empty().templates),
        stories=hash(StoryGraph([])),
        nlu=hash(TrainingData()),
        rasa_version=rasa.__version__,
    )

    actual = await model_fingerprint(project_files)
    assert actual[FINGERPRINT_TRAINED_AT_KEY] is not None

    del actual[FINGERPRINT_TRAINED_AT_KEY]
    del expected[FINGERPRINT_TRAINED_AT_KEY]

    assert actual == expected


@pytest.mark.parametrize("use_fingerprint", [True, False])
async def test_rasa_packaging(trained_model, project, use_fingerprint):
    unpacked_model_path = get_model(trained_model)

    os.remove(os.path.join(unpacked_model_path, FINGERPRINT_FILE_PATH))
    if use_fingerprint:
        fingerprint = await model_fingerprint(_project_files(project))
    else:
        fingerprint = None

    tempdir = tempfile.mkdtemp()
    output_path = os.path.join(tempdir, "test.tar.gz")

    create_package_rasa(unpacked_model_path, output_path, fingerprint)

    unpacked = get_model(output_path)

    assert (
        os.path.exists(os.path.join(unpacked, FINGERPRINT_FILE_PATH)) == use_fingerprint
    )
    assert os.path.exists(os.path.join(unpacked, DEFAULT_CORE_SUBDIRECTORY_NAME))
    assert os.path.exists(os.path.join(unpacked, "nlu"))

    assert not os.path.exists(unpacked_model_path)


@pytest.mark.parametrize(
    "fingerprint",
    [
        {
            "new": _fingerprint(),
            "old": _fingerprint(stories=["others"]),
            "retrain_core": True,
            "retrain_nlu": [],
            "retrain_nlg": True,
        },

        {
            "new": _fingerprint(nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "old": _fingerprint(),
            "retrain_core": False,
            "retrain_nlu": ["fr"],
            "retrain_nlg": False,
        },
        {
            "new": _fingerprint(nlu={"en": "test_en_changed", "fr": "test_fr_changed"}),
            "old": _fingerprint(),
            "retrain_core": False,
            "retrain_nlu": ["en", "fr"],
        },
        {
            "new": _fingerprint(nlu={"en": "test_en_changed", "fr": "test_fr"}),
            "old": _fingerprint(),
            "retrain_core": False,
            "retrain_nlu": ["en"],
        },
        {
            "new": _fingerprint(config="others"),
            "old": _fingerprint(nlu={"en": "test_en_changed", "fr": "test_fr"}),
            "retrain_core": True,
            "retrain_nlu": ["en", "fr"],
            "retrain_nlg": True,
        },
        {
            "new": _fingerprint(config_core="others"),
            "old": _fingerprint(),
            "retrain_core": True,
            "retrain_nlu": [],
            "retrain_nlg": True,
        },
        {
            "new": _fingerprint(config_nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "old": _fingerprint(),
            "retrain_core": False,
            "retrain_nlu": ["fr"],
        },
        {
            "new": _fingerprint(config_nlu={"en": "test_en_changed", "fr": "test_fr_changed"}),
            "old": _fingerprint(),
            "retrain_core": False,
            "retrain_nlu": ["en", "fr"],
        },
        {
            "new": _fingerprint(config_nlu={"en": "test_en_changed", "fr": "test_fr"}),
            "old": _fingerprint(),
            "retrain_core": False,
            "retrain_nlu": ["en"],
            "retrain_nlg": False,
        },
        {
            "new": _fingerprint(),
            "old": _fingerprint(),
            "retrain_core": False,
            "retrain_nlu": [],
            "retrain_nlg": False,
        },
        {
            "new": _fingerprint(nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "old": _fingerprint(nlu={}, config_nlu={}),
            "retrain_core": False,
            "retrain_nlu": ["en", "fr"],
        },
        {
            "new": _fingerprint(nlu={}),
            "old": _fingerprint(nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "retrain_core": False,
            "retrain_nlu": ["en", "fr"],
        },
        {
            "old": _fingerprint(nlu={}, config_nlu={}),
            "new": _fingerprint(nlu={"en": "test_en"}, config_nlu={"en": "test_en"}),
            "retrain_core": False,
            "retrain_nlu": ["en"],
        },
        {
            "old": _fingerprint(nlu={"en": "test_en"}, config_nlu={"en": "test_en"}),
            "new": _fingerprint(nlu={"en": "test_en", "fr": "test_fr_changed"}, config_nlu={"en": "test_en", "fr": "test_fr_changed"}),
            "retrain_core": False,
            "retrain_nlu": ["fr"],
        },
        {
            "new": _fingerprint(nlu={"en": "test_en_changed", "fr": "test_fr"}, config_nlu={"en": "test_en", "fr": "test_fr"}),
            "old": _fingerprint(nlu={"en": "test_en", "fr": "test_fr"}, config_nlu={"en": "test_en", "fr": "test_fr"}),
            "retrain_core": False,
            "retrain_nlu": ["en"],
        },
        # {
        #     "old": _fingerprint(config_nlu={"en": "en"}, nlu={}),
        #     "new": _fingerprint(config_nlu={"en": "en"}, nlu={"en": "test_en"}),
        #     "retrain_core": False,
        #     "retrain_nlu": ["en"],
        # },
    ],
)
def test_should_retrain(trained_model: Text, fingerprint: Fingerprint):
    old_model = set_fingerprint(trained_model, fingerprint["old"])

    retrain = should_retrain(fingerprint["new"], old_model, tempfile.mkdtemp())

    assert retrain.should_retrain_core() == fingerprint["retrain_core"]
    assert retrain.should_retrain_nlg() == fingerprint["retrain_nlg"]
    assert retrain.should_retrain_nlu() == fingerprint["retrain_nlu"]


def set_fingerprint(trained_model: Text, fingerprint: Fingerprint) -> Text:
    unpacked_model_path = get_model(trained_model)

    os.remove(os.path.join(unpacked_model_path, FINGERPRINT_FILE_PATH))

    tempdir = tempfile.mkdtemp()
    output_path = os.path.join(tempdir, "test.tar.gz")

    create_package_rasa(unpacked_model_path, output_path, fingerprint)

    return output_path


@pytest.mark.parametrize(
    "comparison_result,retrain_all,retrain_core,retrain_nlg,retrain_nlu",
    [
        (FingerprintComparisonResult(force_training=True), True, True, True, True),
        (
            FingerprintComparisonResult(core=True, nlu=False, nlg=False),
            True,
            True,
            True,
            False,
        ),
        (
            FingerprintComparisonResult(core=False, nlu=True, nlg=False),
            True,
            False,
            False,
            True,
        ),
        (
            FingerprintComparisonResult(core=True, nlu=True, nlg=False),
            True,
            True,
            True,
            True,
        ),
    ],
)
def test_fingerprint_comparison_result(
    comparison_result: FingerprintComparisonResult,
    retrain_all: bool,
    retrain_core: bool,
    retrain_nlg: bool,
    retrain_nlu: bool,
):
    assert comparison_result.is_training_required() == retrain_all
    assert comparison_result.should_retrain_core() == retrain_core
    assert comparison_result.should_retrain_nlg() == retrain_nlg
    assert comparison_result.should_retrain_nlu() == retrain_nlu


async def test_update_with_new_domain(trained_model: Text, tmpdir: Path):
    _ = model.unpack_model(trained_model, tmpdir)

    new_domain = Domain.empty()

    mocked_importer = Mock()

    async def get_domain() -> Domain:
        return new_domain

    mocked_importer.get_domain = get_domain

    await model.update_model_with_new_domain(mocked_importer, tmpdir)

    actual = Domain.load(tmpdir / DEFAULT_CORE_SUBDIRECTORY_NAME / DEFAULT_DOMAIN_PATH)

    assert actual.is_empty()
