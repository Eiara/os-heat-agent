import pytest
import requests_mock
from os_heat_agent import dynamically_fetch_region

@pytest.mark.parametrize("load_metadata",
  ["good_meta_data.json"],
  indirect=True
)
def test_dynamically_fetch_region_good(load_metadata):
  with requests_mock.Mocker() as mock:
    mock.get("http://169.254.169.254/openstack/latest/meta_data.json", json=load_metadata)
    assert dynamically_fetch_region() == load_metadata["availability_zone"][:-1]

@pytest.mark.parametrize("load_metadata",
  ["bad_meta_data.json"],
  indirect=True
)
def test_dynamically_fetch_region_bad(load_metadata):
  with requests_mock.Mocker() as mock:
    mock.get("http://169.254.169.254/openstack/latest/meta_data.json", json=load_metadata)
    with pytest.raises(KeyError):
      dynamically_fetch_region()