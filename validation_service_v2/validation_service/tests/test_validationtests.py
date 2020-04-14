import os
from datetime import datetime
from time import sleep
from urllib.parse import urlparse
import logging

from fastapi import status
from fastapi.testclient import TestClient

from ..main import app
from ..data_models import (BrainRegion, Species, ImplementationStatus,
                           ScoreType, RecordingModality, ValidationTestType)

client = TestClient(app)
token = os.environ["VF_TEST_TOKEN"]
AUTH_HEADER = {"Authorization": f"Bearer {token}"}


def check_validation_test(test_definition):
    assert isinstance(test_definition["name"], str)
    assert isinstance(test_definition["description"], str)
    if test_definition["alias"]:
        assert isinstance(test_definition["alias"], str)
        assert " " not in test_definition["alias"]
    assert isinstance(test_definition["author"], list)
    assert len(test_definition["author"]) > 0
    assert "family_name" in test_definition["author"][0]
    if test_definition["brain_region"]:
        assert test_definition["brain_region"] in [item.value for item in BrainRegion]
    if test_definition["species"]:
        assert test_definition["species"] in [item.value for item in Species]
    assert test_definition["status"] in [item.value for item in ImplementationStatus]
    if test_definition["score_type"]:
        assert test_definition["score_type"] in [item.value for item in ScoreType]
    if test_definition["test_type"]:
        assert test_definition["test_type"] in [item.value for item in ValidationTestType]
    if test_definition["data_modality"]:
        assert test_definition["data_modality"] in [item.value for item in RecordingModality]
    if test_definition["data_location"]:
        for url in test_definition["data_location"]:
            assert_is_valid_url(url)
    if test_definition["instances"]:
        check_validation_test_instance(test_definition["instances"][0])


def check_validation_test_instance(test_instance):
    datetime.fromisoformat(test_instance["timestamp"])
    assert isinstance(test_instance["version"], str)
    assert_is_valid_url(test_instance["repository"])


def assert_is_valid_url(url):
    try:
        urlparse(url)
    except ValueError:
        raise AssertionError


def test_get_validation_test_by_id_no_auth():
    test_ids = ("01c68387-fcc4-4fd3-85f0-6eb8ce4467a1",)
    for validation_test_uuid in test_ids:
        response = client.get(f"/tests/{validation_test_uuid}")
        assert response.status_code == 403
        assert response.json() == {
            "detail": "Not authenticated"
        }


def test_get_validation_test_by_id(caplog):
    #caplog.set_level(logging.DEBUG)
    test_ids = ("01c68387-fcc4-4fd3-85f0-6eb8ce4467a1",)
    for validation_test_uuid in test_ids:
        # first is private (but test user has access), second is public
        # todo: test with a second user, who does not have access
        response = client.get(f"/tests/{validation_test_uuid}", headers=AUTH_HEADER)
        assert response.status_code == 200
        validation_test = response.json()
        check_validation_test(validation_test)


def test_list_validation_tests_no_auth():
    response = client.get(f"/tests/")
    assert response.status_code == 403
    assert response.json() == {
        "detail": "Not authenticated"
    }


def test_list_validation_tests_nofilters():
    response = client.get(f"/tests/?size=5", headers=AUTH_HEADER)
    assert response.status_code == 200
    validation_tests = response.json()
    assert len(validation_tests) == 5
    for validation_test in validation_tests:
        check_validation_test(validation_test)


def test_list_validation_tests_filter_by_brain_region():
    response = client.get(f"/tests/?size=5&brain_region=hippocampus", headers=AUTH_HEADER)
    assert response.status_code == 200
    validation_tests = response.json()
    assert len(validation_tests) == 5
    for validation_test in validation_tests:
        check_validation_test(validation_test)
        assert validation_test["brain_region"] == "hippocampus"


def test_list_validation_tests_filter_by_species():
    response = client.get(f"/tests/?size=5&species=Rattus%20norvegicus", headers=AUTH_HEADER)
    assert response.status_code == 200
    validation_tests = response.json()
    assert len(validation_tests) == 5
    for validation_test in validation_tests:
        check_validation_test(validation_test)
        assert validation_test["species"] == Species.rat  # "Rattus norvegicus"


def test_list_validation_tests_filter_by_author():
    response = client.get(f"/tests/?size=5&author=Appukuttan", headers=AUTH_HEADER)
    assert response.status_code == 200
    validation_tests = response.json()
    assert len(validation_tests) == 5
    for validation_test in validation_tests:
        check_validation_test(validation_test)
        assert len([author["family_name"] == "Appukuttan" for author in validation_test["author"]]) > 0


def test_list_validation_tests_filter_by_brain_region_and_authors():
    response = client.get(f"/tests/?size=5&brain_region=hippocampus&author=Appukuttan", headers=AUTH_HEADER)
    assert response.status_code == 200
    validation_tests = response.json()
    assert len(validation_tests) == 5
    for validation_test in validation_tests:
        check_validation_test(validation_test)
        assert len([author["family_name"] == "Appukuttan" for author in validation_test["author"]]) > 0
        assert validation_test["brain_region"] == "hippocampus"


def _build_sample_validation_test():
    now = datetime.now()
    return {
        "name": f"TestValidationTestDefinition API v2 {now.isoformat()}",
        "alias": f"TestValidationTestDefinition-APIv2-{now.isoformat()}",
        "author": [
            {
            "given_name": "Frodo",
            "family_name": "Baggins"
            },
            {
            "given_name": "Tom",
            "family_name": "Bombadil"
            }
        ],
        "status": "proposal",
        "species": "Mus musculus",
        "brain_region": "hippocampus",
        "cell_type": "hippocampus CA1 pyramidal cell",
        "description": "description goes here",
        "data_location": ["http://example.com/my_data.csv"],
        "data_type": "csv",
        "data_modality": "electrophysiology",
        "test_type": "single cell activity",
        "score_type": "z-score",
        "instances": [
            {
            "version": "1.23",
            "description": "description of this version",
            "parameters": "{'meaning': 42}",
            "path": "mylib.tests.MeaningOfLifeTest",
            "repository": "http://example.com/my_code.py"
            }
        ]
    }

def test_create_and_delete_validation_test_definition(caplog):
    caplog.set_level(logging.DEBUG)

    payload = _build_sample_validation_test()
    # create
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == 201
    posted_validation_test = response.json()
    check_validation_test(posted_validation_test)

    # check we can retrieve validation_test
    validation_test_uuid = posted_validation_test["id"]
    response = client.get(f"/tests/{validation_test_uuid}", headers=AUTH_HEADER)
    assert response.status_code == 200
    retrieved_validation_test = response.json()
    assert retrieved_validation_test == posted_validation_test

    # delete again
    response = client.delete(f"/tests/{validation_test_uuid}", headers=AUTH_HEADER)
    assert response.status_code == 200

    # todo: check validation_test no longer exists
    response = client.get(f"/tests/{validation_test_uuid}", headers=AUTH_HEADER)
    assert response.status_code == 404


def test_create_validation_test_with_invalid_data():
    # missing required validation_test project fields
    for required_field in ("name", "author", "description"):
        payload = _build_sample_validation_test()
        del payload[required_field]
        response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {
            'detail': [
                {'loc': ['body', 'test', required_field],
                 'msg': 'field required',
                 'type': 'value_error.missing'}
            ]
        }
    # missing required validation_test instance fields
    for required_field in ("version",):
        payload = _build_sample_validation_test()
        del payload["instances"][0][required_field]
        response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {
            'detail': [
                {'loc': ['body', 'test', 'instances', 0, required_field],
                 'msg': 'field required',
                 'type': 'value_error.missing'}
            ]
        }
    # invalid value for Enum field
    payload = _build_sample_validation_test()
    payload["species"] = "klingon"
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    err_msg = response.json()["detail"]
    assert err_msg[0]['loc'] == ['body', 'test', 'species']
    assert err_msg[0]['msg'].startswith('value is not a valid enumeration member')
    assert err_msg[0]['type'] == 'type_error.enum'
    # invalid URL
    payload = _build_sample_validation_test()
    payload["instances"][0]["repository"] = "/filesystem/path/to/doc.txt"
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {'loc': ['body', 'test', 'instances', 0, 'repository'],
             'msg': 'invalid or missing URL scheme',
             'type': 'value_error.url.scheme'}
        ]
    }
    # incorrectly formatted "author" field
    payload = _build_sample_validation_test()
    payload["author"] = ["Thorin Oakenshield"]
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'detail': [
            {'loc': ['body', 'test', 'author', 0],
             'msg': 'value is not a valid dict',
             'type': 'type_error.dict'}
        ]
    }


def test_create_validation_test_with_existing_alias():
    payload = _build_sample_validation_test()
    payload["alias"] = "bpo_efel"
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        'detail': "Another validation test with alias 'bpo_efel' already exists."
    }


def test_create_duplicate_validation_test(caplog):
    # Creating two validation_tests with the same name and date_created fields is not allowed
    #caplog.set_level(logging.INFO)
    payload = _build_sample_validation_test()
    # create
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == 201
    posted_validation_test = response.json()
    check_validation_test(posted_validation_test)

    # try to create the same again, copying the date_created from the original
    payload["date_created"] = posted_validation_test["date_created"]
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        'detail': 'Another validation test with the same name and timestamp already exists.'
    }

    # delete first validation_test
    response = client.delete(f"/tests/{posted_validation_test['id']}", headers=AUTH_HEADER)
    assert response.status_code == 200

    # todo: now try to create same again - should now work (set deprecated from True to False)


def test_update_validation_test(caplog):
    #caplog.set_level(logging.INFO)
    payload = _build_sample_validation_test()
    # create
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == 201
    posted_validation_test = response.json()
    check_validation_test(posted_validation_test)
    # make changes
    changes = {
        "alias": posted_validation_test["alias"] + "-changed",
        "name": posted_validation_test["name"] + " (changed)",  # as long as date_created is not changed, name can be
        "author": [{
            "given_name": "Tom",
            "family_name": "Bombadil"
        }],
        "data_modality": "fMRI",
        "description": "The previous description was too short"
    }
    # update
    response = client.put(f"/tests/{posted_validation_test['id']}", json=changes, headers=AUTH_HEADER)
    assert response.status_code == 200
    updated_validation_test = response.json()
    check_validation_test(updated_validation_test)

    assert posted_validation_test["id"] == updated_validation_test["id"]
    assert posted_validation_test["instances"] == updated_validation_test["instances"]
    assert updated_validation_test["data_modality"] != payload["data_modality"]
    assert updated_validation_test["data_modality"] == changes["data_modality"] == "fMRI"

    # delete validation_test
    response = client.delete(f"/tests/{posted_validation_test['id']}", headers=AUTH_HEADER)
    assert response.status_code == 200


def test_update_validation_test_with_invalid_data():
    payload = _build_sample_validation_test()
    # create
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == 201
    posted_validation_test = response.json()
    check_validation_test(posted_validation_test)
    # mix valid and invalid changes
    # none of them should be applied
    changes = {
        "alias": posted_validation_test["alias"] + "-changed",
        "name": posted_validation_test["name"] + " (changed)",  # as long as date_created is not changed, name can be
        "author": None,  # invalid
        "data_modality": "foo",  # invalid
        "description": None   # invalid
    }
    response = client.put(f"/tests/{posted_validation_test['id']}", json=changes, headers=AUTH_HEADER)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errmsg = response.json()["detail"]
    assert set([part['loc'][-1] for part in errmsg]) == set(['author', 'data_modality', 'description'])

    # delete validation_test
    response = client.delete(f"/tests/{posted_validation_test['id']}", headers=AUTH_HEADER)
    assert response.status_code == 200


def test_changing_to_invalid_alias():
    # expect 409
    payload = _build_sample_validation_test()
    # create
    response = client.post(f"/tests/", json=payload, headers=AUTH_HEADER)
    assert response.status_code == 201
    posted_validation_test = response.json()
    check_validation_test(posted_validation_test)

    changes = {"alias": "bpo_efel"}
    response = client.put(f"/tests/{posted_validation_test['id']}", json=changes, headers=AUTH_HEADER)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Another validation test with alias 'bpo_efel' already exists."

    # delete validation_test
    response = client.delete(f"/tests/{posted_validation_test['id']}", headers=AUTH_HEADER)
    assert response.status_code == 200



def test_list_validation_test_instances_by_validation_test_id():
    validation_test_uuid = "01c68387-fcc4-4fd3-85f0-6eb8ce4467a1"
    response1 = client.get(f"/tests/{validation_test_uuid}", headers=AUTH_HEADER)
    assert response1.status_code == 200
    test_definition = response1.json()
    response2 = client.get(f"/tests/{validation_test_uuid}/instances/", headers=AUTH_HEADER)
    assert response2.status_code == 200
    validation_test_instances = response2.json()
    assert len(validation_test_instances) > 0

    assert test_definition["instances"] == validation_test_instances


def test_get_validation_test_instance_by_id():
    instance_uuid = "46e376a8-8c46-44ce-aa76-020d35114703"
    response = client.get(f"/tests/query/instances/{instance_uuid}", headers=AUTH_HEADER)
    assert response.status_code == 200
    validation_test_instance = response.json()
    check_validation_test_instance(validation_test_instance)


def test_get_validation_test_instance_by_project_and_id():
    validation_test_uuid  = "01c68387-fcc4-4fd3-85f0-6eb8ce4467a1"
    instance_uuid = "46e376a8-8c46-44ce-aa76-020d35114703"
    response = client.get(f"/tests/{validation_test_uuid}/instances/{instance_uuid}", headers=AUTH_HEADER)
    assert response.status_code == 200
    validation_test_instance = response.json()
    check_validation_test_instance(validation_test_instance)
