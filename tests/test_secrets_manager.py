"""Testing for Secrets that emit by the stacks"""
from tests.parent_testcase import ParentTestCase


class TestSecretsManager(ParentTestCase):
    """Testing for Secrets that emit by the stacks"""

    def test_secrets_exists(self):
        """should have secrets created """
        result = self.sec_man_client.list_secrets()
        # result should be 2 if Oracle is skipped. if it's not skipped it should be three
        self.assertEqual(len(result["SecretList"]), 2)
