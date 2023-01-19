"""Testing for cloudwatch stack"""
from tests.parent_testcase import ParentTestCase


class TestCloudWatch(ParentTestCase):
    """Testing for cloudwatch stack"""

    def test_cw_metrics(self):
        """Testing for generated metrics in CW"""

        instances = set()
        result = self.cw_client.list_metrics(Namespace="CWAgent", MetricName="cpu_usage_system")
        for i in result["Metrics"]:
            instances.add(i["Dimensions"][0]["Value"])

        for key, value in self.cdk_output_map.items():
            if "Instance" in key:
                self.assertTrue(value in instances)
