"""Nested Stack for creating VPC endpoint"""
from typing import List, Dict

from aws_cdk import (
    aws_ec2 as _ec2,
    aws_iam as _iam
)
from aws_cdk import NestedStack
from constructs import Construct


class SwiftVPCEndpoints(NestedStack):
    """Nested Stack for creating VPC endpoint"""

    # pylint: disable=too-many-arguments
    def __init__(self, scope: Construct, cid: str, application_names: List[str],
                 instance_ids: Dict[str, List[str]],
                 instance_roles_map: Dict[str, _iam.IRole],
                 endpoint_sg: _ec2.ISecurityGroup,
                 vpc: _ec2.Vpc) -> None:

        super().__init__(scope, cid)
        principals = []

        for application_name in application_names:
            for instance_id in instance_ids[application_name]:
                principals.append(_iam.ArnPrincipal(
                    arn="arn:aws:sts::" + self.account + ":assumed-role/" +
                        instance_roles_map[application_name].role_name + "/" + instance_id))

        self.create_interface_endpoint(
            "ssm", security_group=endpoint_sg,
            interface_endpoint_policy=
            _iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                 actions=["ssm:DescribeAssociation",
                                          "ssm:GetDeployablePatchSnapshotForInstance",
                                          "ssm:GetDocument",
                                          "ssm:DescribeDocument",
                                          "ssm:GetManifest",
                                          "ssm:GetParameter",
                                          "ssm:GetParameters",
                                          "ssm:ListAssociations",
                                          "ssm:ListInstanceAssociations",
                                          "ssm:PutInventory",
                                          "ssm:PutComplianceItems",
                                          "ssm:PutConfigurePackageResult",
                                          "ssm:UpdateAssociationStatus",
                                          "ssm:UpdateInstanceAssociationStatus",
                                          "ssm:UpdateInstanceInformation"], resources=["*"],
                                 principals=principals), vpc=vpc)
        self.create_interface_endpoint(
            "ec2", security_group=endpoint_sg,
            interface_endpoint_policy=
            _iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                 actions=["ec2:Describe*"], resources=["*"],
                                 principals=principals), vpc=vpc)
        self.create_interface_endpoint(
            "ssmmessages", security_group=endpoint_sg,
            interface_endpoint_policy=
            _iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                 actions=["ssmmessages:CreateControlChannel",
                                          "ssmmessages:CreateDataChannel",
                                          "ssmmessages:OpenControlChannel",
                                          "ssmmessages:OpenDataChannel"], resources=["*"],
                                 principals=principals), vpc=vpc)
        self.create_interface_endpoint(
            "ec2messages", security_group=endpoint_sg,
            interface_endpoint_policy=
            _iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                 actions=["ec2messages:AcknowledgeMessage",
                                          "ec2messages:DeleteMessage",
                                          "ec2messages:FailMessage",
                                          "ec2messages:GetEndpoint",
                                          "ec2messages:GetMessages",
                                          "ec2messages:SendReply"], resources=["*"],
                                 principals=principals), vpc=vpc)
        self.create_interface_endpoint(
            "logs", security_group=endpoint_sg,
            interface_endpoint_policy=
            _iam.PolicyStatement(effect=_iam.Effect.ALLOW, actions=["logs:PutLogEvents",
                                                                    "logs:DescribeLogStreams",
                                                                    "logs:DescribeLogGroups",
                                                                    "logs:CreateLogStream",
                                                                    "logs:CreateLogGroup"],
                                 resources=["*"],
                                 principals=principals), vpc=vpc)
        self.create_interface_endpoint(
            "monitoring", security_group=endpoint_sg,
            interface_endpoint_policy=
            _iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                 actions=["cloudwatch:PutMetricData"], resources=["*"],
                                 principals=principals), vpc=vpc)

        self.create_gateway_endpoint(
            "s3", vpc=vpc,
            gateway_endpoint_policy=
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["s3:GetObject",
                         "s3:PutObject"],
                resources=[
                    "arn:aws:s3:::aws-ssm-" + self.region + "/*",
                    "arn:aws:s3:::aws-windows-downloads-" + self.region + "/*",
                    "arn:aws:s3:::amazon-ssm-" + self.region + "/*",
                    "arn:aws:s3:::amazon-ssm-packages-" + self.region + "/*",
                    "arn:aws:s3:::" + self.region + "-birdwatcher-prod/*",
                    "arn:aws:s3:::aws-ssm-distributor-file-" + self.region + "/*",
                    "arn:aws:s3:::patch-baseline-snapshot-" + self.region + "/*",
                    "arn:aws:s3:::amazoncloudwatch-agent-" + self.region + "/*",
                    "arn:aws:s3:::" + self.node.try_get_context("qs_s3_bucket") +
                    "-" + self.region + "/*"],
                principals=[_iam.AnyPrincipal()]))

    def create_interface_endpoint(self, service_name: str, security_group: _ec2.ISecurityGroup,
                                  vpc: _ec2.Vpc,
                                  interface_endpoint_policy: _iam.PolicyStatement = None):
        """create interface endpoint"""
        vpc_endpoint = _ec2.InterfaceVpcEndpoint(
            self, id=service_name.upper() + "VPCEndPoint",
            vpc=vpc,
            service=_ec2.InterfaceVpcEndpointAwsService(service_name),
            private_dns_enabled=True,
            security_groups=[security_group]
        )
        if interface_endpoint_policy is not None:
            vpc_endpoint.add_to_policy(interface_endpoint_policy)

    def create_gateway_endpoint(self, service_name: str, vpc: _ec2.Vpc,
                                gateway_endpoint_policy: _iam.PolicyStatement = None):
        """create gateway endpoint"""
        vpc_endpoint = _ec2.GatewayVpcEndpoint(
            self, id=service_name.upper() + "VPCEndPoint", vpc=vpc,
            service=_ec2.InterfaceVpcEndpointAwsService(service_name))

        if gateway_endpoint_policy is not None:
            vpc_endpoint.add_to_policy(gateway_endpoint_policy)
