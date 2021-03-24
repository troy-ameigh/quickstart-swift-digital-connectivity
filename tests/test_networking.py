"""Testing for networking stack"""
from tests.parent_testcase import ParentTestCase


class TestNetworking(ParentTestCase):
    """Testing for networking stack"""

    def setUp(self):
        super().setUp()
        self.vpc_id = self.cdk_output_map.get("VPCID")
        if not self.vpc_id:
            self.vpc_id = "vpc-08a9146ce19dfa1ef"

    def test_no_igw(self):
        """should not have igw attached """
        result = self.ec2_client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id',
                                                                      'Values': [
                                                                          self.vpc_id,
                                                                      ]}])

        self.assertFalse(result["InternetGateways"])

    def test_vgw(self):
        """should have vgw attached """
        result = self.ec2_client.describe_vpn_gateways(Filters=[{'Name': 'attachment.vpc-id',
                                                                 'Values': [
                                                                     self.vpc_id,
                                                                 ]}])
        self.assertTrue(result["VpnGateways"])
