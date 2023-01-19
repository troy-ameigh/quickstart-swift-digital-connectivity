"""test SSM session manager connection with ec2 instances"""
from tests.parent_testcase import ParentTestCase


class TestSSMSessionConnection(ParentTestCase):
    """test SSM session manager connection with ec2 instances"""

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.snl_session_id = None
        self.amh_session_id = None
        self.session_ids = []

    def tearDown(self) -> None:

        for session_id in self.session_ids:
            self.ssm_client.terminate_session(SessionId=session_id)

    def test_snl_ssm_connection(self):
        """test SSM session manager connection with sag snl ec2 instances"""
        self.common_test_ssm_connection("SAGSNL")

    def test_amh_ssm_connection(self):
        """test SSM session manager connection with amh instances"""
        self.common_test_ssm_connection("AMH")

    def common_test_ssm_connection(self, component: str):
        """test SSM session manager connection with any instances"""
        for i in range(1, 3):
            result = self.ssm_client.start_session(
                Target=self.cdk_output_map.get(component + str(i) + "InstanceID"))
            session_id = result.get("SessionId")
            self.assertIsNotNone(session_id)
            self.session_ids.append(session_id)
