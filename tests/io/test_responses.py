import pytest
from unittest import mock
import requests_mock
import boto3
from os_heat_agent.heat import get_config
from os_heat_agent import dynamically_fetch_region
import json

def MockCFNResource(**kwargs):
  return [{}]

def MockCFNResponse(**kwargs):
  pass

@pytest.mark.parametrize("load_heat_stack_response",
  ["babashka/good_create_response.json"],
  indirect=True
)
@mock.patch("boto3.session.Session")
def test_good_response(mock_session_class, load_heat_stack_response):
  mock_session_obj = mock.Mock()
  mock_client_obj = mock.Mock()

  mock_client_obj.describe_stack_resource.return_value = load_heat_stack_response
  mock_session_obj.client.return_value = mock_client_obj
  mock_session_class.return_value = mock_session_obj

  cfg = {
    "stack_name": "asdf",
    "access_key_id": "asdf",
    "secret_access_key": "asdf2",
    "metadata_url": "http://192.168.1.1/",
    "path": "foo.bar"
  }
  get_config(cfg, "region")

##
## Test the dynamic region fetching code
## 

