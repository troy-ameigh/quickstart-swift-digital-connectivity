"""Class for SWIFT specific security"""
import boto3
from aws_cdk import (
    aws_ec2 as _ec2,
)
from constructs import Construct
from utilities.swift_components import SwiftComponents
from security.generic_security import GenericSecurity


class SWIFTSecurity(GenericSecurity):
    """Class for SWIFT specific security, inherit from generic security"""
    # pylint: disable=too-many-arguments
    def __init__(self, scope: Construct, cid: str,
                 vpc: _ec2.Vpc,
                 swift_ip_range: str = "149.134.0.0/16",
                 hsm_ip: str = "10.20.1.10/32",
                 workstation_ip_range: str = "10.1.0.0/16", **kwargs) -> None:
        super().__init__(scope, cid, vpc, **kwargs)
        self._swift_ip_range = swift_ip_range
        self._hsm_ip = hsm_ip
        self._workstation_ip_range = workstation_ip_range
        self.create_security_group("VPCEndpointSG")

    def enforce_security_groups_rules(self) -> None:
        """enforcing security group rule. ie creating security group rule """
        sagsnl_sg = self.get_security_group(SwiftComponents.SAGSNL + "SG")
        rds_sg = self.get_security_group("RDSSG")
        mq_sg = self.get_security_group("MQSG")
        amh_sg = self.get_security_group(SwiftComponents.AMH + "SG")

        boto = boto3.client("ec2")
        prefix_lists = boto.describe_prefix_lists(
            Filters=[{"Name": "prefix-list-name", "Values": ["com.amazonaws.*.s3"]}])
        s3_prefix_list = prefix_lists["PrefixLists"][0]["PrefixListId"]

        sagsnl_sg.connections.allow_from(other=amh_sg,
                                         port_range=_ec2.Port(
                                             protocol=_ec2.Protocol.TCP,
                                             string_representation="SAGSNL- AMH (48002,48003)",
                                             from_port=48002,
                                             to_port=48003
                                         ),
                                         description="Incoming connection from AMH")

        self.add_security_group_rule(SwiftComponents.SAGSNL + "SG", protocol=_ec2.Protocol.TCP,
                                     cidr_range=self._workstation_ip_range,
                                     from_port=2443, to_port=2443, is_ingress=True,
                                     description="SWP Web GUI Interface Ingress from workstation"
                                     )
        self.add_security_group_rule(SwiftComponents.SAGSNL + "SG", protocol=_ec2.Protocol.TCP,
                                     prefix_list=s3_prefix_list,
                                     from_port=443, to_port=443, is_ingress=False,
                                     description="Egress to S3 VPC Gateway Endpoint"
                                     )
        self.add_security_group_rule(SwiftComponents.SAGSNL + "SG", protocol=_ec2.Protocol.ALL,
                                     cidr_range=self._swift_ip_range,
                                     from_port=0, to_port=65535, is_ingress=False,
                                     description="To SWIFT via VGW and VPN"
                                     )
        self.add_security_group_rule(SwiftComponents.SAGSNL + "SG", protocol=_ec2.Protocol.TCP,
                                     cidr_range=self._hsm_ip,
                                     from_port=1792, to_port=1792, is_ingress=False,
                                     description="To HSM via VGW"
                                     )
        self.add_security_group_rule(SwiftComponents.SAGSNL + "SG", protocol=_ec2.Protocol.TCP,
                                     cidr_range=self._hsm_ip,
                                     from_port=22, to_port=22, is_ingress=False,
                                     description="To HSM (SSH) via VGW"
                                     )
        self.add_security_group_rule(SwiftComponents.SAGSNL + "SG", protocol=_ec2.Protocol.TCP,
                                     cidr_range=self._hsm_ip,
                                     from_port=48321, to_port=48321, is_ingress=False,
                                     description="TO HSM (Remote PED) via VGW "
                                     )

        amh_sg.connections.allow_to(other=sagsnl_sg,
                                    port_range=_ec2.Port(
                                        protocol=_ec2.Protocol.TCP,
                                        string_representation="AMH - SAGSNL (48002, 48003)",
                                        from_port=48002,
                                        to_port=48003
                                    ),
                                    description="AMH to SAGSNL connection")

        amh_sg.connections.allow_to(other=rds_sg,
                                    port_range=_ec2.Port(
                                        protocol=_ec2.Protocol.TCP,
                                        string_representation="RDS (1521)",
                                        from_port=1521,
                                        to_port=1521
                                    ),
                                    description="AMH - RDS (1521)")
        amh_sg.connections.allow_to(other=mq_sg,
                                    port_range=_ec2.Port(
                                        protocol=_ec2.Protocol.TCP,
                                        string_representation="MQ (61617)",
                                        from_port=61617,
                                        to_port=61617
                                    ),
                                    description="AMH - MQ (61617)")
        self.add_security_group_rule(SwiftComponents.AMH + "SG", protocol=_ec2.Protocol.TCP,
                                     prefix_list=s3_prefix_list,
                                     from_port=443, to_port=443,
                                     is_ingress=False,
                                     description="AMH Egress to S3"
                                     )
        self.add_security_group_rule(SwiftComponents.AMH + "SG", protocol=_ec2.Protocol.TCP,
                                     cidr_range=self._workstation_ip_range,
                                     from_port=8443, to_port=8443, is_ingress=True
                                     )
        rds_sg.connections.allow_from(other=amh_sg,
                                      port_range=_ec2.Port(
                                          protocol=_ec2.Protocol.TCP,
                                          string_representation="RDS (1521)",
                                          from_port=1521,
                                          to_port=1521
                                      ),
                                      description="AMH - RDS (1521)")

        mq_sg.connections.allow_from(other=amh_sg,
                                     port_range=_ec2.Port(
                                         protocol=_ec2.Protocol.TCP,
                                         string_representation="MQ (61617)",
                                         from_port=61617,
                                         to_port=61617
                                     ),
                                     description="AMH - MQ (61617)")
        self.add_security_group_rule("MQSG", protocol=_ec2.Protocol.TCP,
                                     cidr_range=self._workstation_ip_range,
                                     from_port=8162, to_port=8162, is_ingress=True
                                     )

    def create_nacls(self) -> None:
        """creating nacl and rules"""
        selection_sagsnl = _ec2.SubnetSelection(subnet_group_name=SwiftComponents.SAGSNL)
        selection_amh = _ec2.SubnetSelection(subnet_group_name=SwiftComponents.AMH)

        self.create_nacl(cid=SwiftComponents.SAGSNL + "NACL", name=SwiftComponents.SAGSNL + "NACL",
                         description="NACL for SAGSNL Subnet",
                         subnet_selection=selection_sagsnl)
        self.create_nacl(cid=SwiftComponents.AMH + "NACL", name=SwiftComponents.AMH + "NACL",
                         description="NACL For AMMH Subnet",
                         subnet_selection=selection_amh)

        self.add_nacl_entry(cid=SwiftComponents.SAGSNL + "NACL",
                            nacl_id="SAGSNLNACLEntry1",
                            cidr=_ec2.AclCidr.any_ipv4(),
                            rule_number=100,
                            traffic=_ec2.AclTraffic.all_traffic(),
                            direction=_ec2.TrafficDirection.EGRESS)
        self.add_nacl_entry(cid=SwiftComponents.SAGSNL + "NACL",
                            nacl_id="SAGSNLNACLEntry2",
                            cidr=_ec2.AclCidr.any_ipv4(),
                            rule_number=100,
                            traffic=_ec2.AclTraffic.all_traffic(),
                            direction=_ec2.TrafficDirection.INGRESS)

        self.add_nacl_entry(cid=SwiftComponents.AMH + "NACL",
                            nacl_id="AMHNACLEntry1",
                            cidr=_ec2.AclCidr.any_ipv4(),
                            rule_number=100,
                            traffic=_ec2.AclTraffic.all_traffic(),
                            direction=_ec2.TrafficDirection.EGRESS)
        self.add_nacl_entry(cid=SwiftComponents.AMH + "NACL",
                            nacl_id="AMHNACLEntry2",
                            cidr=_ec2.AclCidr.any_ipv4(),
                            rule_number=100,
                            traffic=_ec2.AclTraffic.all_traffic(),
                            direction=_ec2.TrafficDirection.INGRESS)
