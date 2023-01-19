"""Parent Test Case """
import json
import os
import unittest
from pathlib import Path

import boto3


class ParentTestCase(unittest.TestCase):
    """Parent Test Case, for base set and teardown """

    def setUp(self):
        region = os.environ.get('AWS_DEFAULT_REGION')
        if not region:
            region = "us-east-1"

        self.ssm_client = boto3.client("ssm")
        self.ec2_client = boto3.client("ec2")
        self.sec_man_client = boto3.client("secretsmanager")
        self.cw_client = boto3.client("cloudwatch")
        filename = region + "_outputs.json"
        self.output_file = open(Path(__file__).parent / ".." / filename, "r")
        cdk_output = json.load(self.output_file)
        self.cdk_output_map = cdk_output.get("SWIFTMain-" + region)

    def tearDown(self) -> None:
        self.output_file.close()
