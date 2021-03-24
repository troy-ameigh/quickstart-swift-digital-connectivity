"""main swift stack"""
from aws_cdk import (
    core,
    aws_ec2 as _ec2
)
from cdk_ec2_key_pair import KeyPair

from cmk.generic_cmk import GenericCMK
from network.generic_network import GenericNetwork
from network.swift_vpc_endpoints import SwiftVPCEndpoints
from security.swift_security import SWIFTSecurity
from swift_amh.swift_amh import SwiftAMH
from swift_database.swift_database import SwiftDatabase
from swift_iam_role.swift_iam_role import SwiftIAMRole
from swift_mq.swift_mq import SwiftMQ
from swift_sagsnl.swift_sagsnl import SwiftSAGSNL
from utilities.swift_components import SwiftComponents


class SwiftMain(core.Stack):
    """main swift stack, for creating nested stack"""

    # pylint: disable=too-many-locals
    def __init__(self, scope: core.Construct, cid: str, **kwargs) -> None:
        super().__init__(scope, cid, **kwargs)

        # Create CMK used by the entire stack
        cmk_stack = GenericCMK(self, "SwiftConnectivityCMK")
        workload_key = cmk_stack.get_cmk()

        # Create networking constructs
        network_stack = GenericNetwork(
            self, "SwiftConnectivityVPC", cidr_range=self.node.try_get_context("vpc_cidr"))
        network_stack.set_vgw(True)
        network_stack.add_isolated_subnets(SwiftComponents.SAGSNL)
        network_stack.add_isolated_subnets(SwiftComponents.AMH)
        network_stack.add_isolated_subnets("Database")
        network_stack.add_isolated_subnets("MQ")
        network_stack.set_vgw_propagation_subnet(
            _ec2.SubnetSelection(subnet_name=SwiftComponents.SAGSNL))
        network_stack.generate()

        # Create security constructs ( IAM Role, SGs, SG Rules, NACLs )
        security_stack = SWIFTSecurity(
            self, "SwiftConnectivitySecurity", vpc=network_stack.get_vpc(),
            swift_ip_range=self.node.try_get_context("swift_ip_range"),
            hsm_ip=self.node.try_get_context("hsm_ip"),
            workstation_ip_range=self.node.try_get_context("workstation_ip_range")
        )

        ops_key_pair: KeyPair = \
            KeyPair(self, "OperatorKeyPair2", name="OperatorKeyPair2",
                    region=self.region,
                    description="KeyPair for the systems operator, just in case."
                    )

        # Create SAGSNL instance , should deploy
        # the instance to the AZ that's according to the provided IP
        sagsnl_ami = self.node.try_get_context("sagsnl_ami")
        if not sagsnl_ami:
            sagsnl_ami = None
        sag_snls = []
        for i in range(1, 3):
            sag_snl = SwiftSAGSNL(
                self, cid=SwiftComponents.SAGSNL + str(i),
                network=network_stack, security=security_stack,
                workload_key=workload_key, ops_key=ops_key_pair,
                private_ip=self.node.try_get_context("sagsnl" + str(i) + "_ip"),
                ami_id=sagsnl_ami,
                vpc_subnets=_ec2.SubnetSelection(
                    availability_zones=[self.availability_zones[i - 1]],
                    subnet_group_name=SwiftComponents.SAGSNL)
            )
            sag_snls.append(sag_snl.get_instance_id())

        amh_ami = self.node.try_get_context("amh_ami")
        if not amh_ami:
            amh_ami = None
        # Create AMH instance
        amhs = []
        for i in range(1, 3):
            amh = SwiftAMH(self, cid=SwiftComponents.AMH + str(i),
                           network=network_stack, security=security_stack,
                           ami_id=amh_ami,
                           workload_key=workload_key,
                           ops_key=ops_key_pair
                           )
            amhs.append(amh.get_instance_id())

        # Create RDS Oracle for AMH to use
        database_stack = SwiftDatabase(self, "Database", network_stack,
                                       security_stack, workload_key)
        # Create Amazon MQ broker for AMH as jms integration
        mq_broker = SwiftMQ(self, "MQMessageBroker", network_stack,
                            security_stack, workload_key)

        # enforce Security group and rule and nacls after the components are created
        security_stack.enforce_security_groups_rules()
        security_stack.create_nacls()

        # Create VPC endpoints and VPC Endpoints policy
        SwiftVPCEndpoints(self, "VPCEndPointStack",
                          application_names=[SwiftComponents.AMH, SwiftComponents.SAGSNL],
                          instance_roles_map=security_stack.get_instance_roles(),
                          endpoint_sg=security_stack.get_security_group("VPCEndpointSG"),
                          vpc=network_stack.get_vpc(),
                          instance_ids={SwiftComponents.AMH: amhs,
                                        SwiftComponents.SAGSNL: sag_snls}
                          )
        for count, value in enumerate(sag_snls):
            core.CfnOutput(self, "SAGSNL" + str(count + 1) + "InstanceID", value=value)
        for count, value in enumerate(amhs):
            core.CfnOutput(self, "AMH" + str(count + 1) + "InstanceID", value=value)
        core.CfnOutput(self, "VPCID", value=network_stack.get_vpc().vpc_id)

        # Create sample role for accessing the components created
        if self.node.try_get_context("create_sample_iam_role") == "true":
            SwiftIAMRole(self, "IAMRole",
                         instance_ids=sag_snls + amhs,
                         database_instance=database_stack.get_db_instance(),
                         mq_broker_arn=mq_broker.get_arn()
                         )
