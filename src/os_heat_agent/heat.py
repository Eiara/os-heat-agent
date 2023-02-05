import boto3
import json
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def get_config(cfn, region):
  
  session = boto3.session.Session()
  logger.debug("Fetching {}", cfn["stack_name"])
  client = session.client(
    # We're using CFN
    service_name="cloudformation", 
    aws_access_key_id = cfn["access_key_id"],
    aws_secret_access_key = cfn["secret_access_key"],
    endpoint_url = cfn["metadata_url"],
    region_name = region
  )
  # We only need the first part of the "path", which will be in the format of some.Path
  resource, field = cfn["path"].split(".", 1)
  
  response = client.describe_stack_resource(
    StackName=cfn["stack_name"],
    LogicalResourceId=resource
  )
  return json.loads(response["StackResourceDetail"]["Metadata"])