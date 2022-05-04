"""Nested Stack for Generic Security"""
from typing import Dict

from aws_cdk import (
    aws_ec2 as _ec2,
    aws_iam as _iam
)
from aws_cdk import NestedStack
from constructs import Construct


class GenericSecurity(NestedStack):
    """Nested Stack for Generic Security, creating security groups, nacls, instance roles"""

    def __init__(self, scope: Construct, cid: str, vpc: _ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, id=cid, **kwargs)
        self._vpc: _ec2.Vpc = vpc
        self._security_groups: {str, _ec2.SecurityGroup} = {}
        self._nacls: {str, _ec2.NetworkAcl} = {}
        self._gateway_endpoints: {str, _ec2.GatewayVpcEndpoint} = {}
        self._instance_role: {str, _iam.Role} = {}

    def get_instance_roles(self) -> Dict[str, _iam.IRole]:
        """getting all instance roles"""
        return self._instance_role

    def get_instance_role(self, name: str) -> _iam.IRole:
        """getting instance role"""
        return self._instance_role.get(name)

    def create_instance_role(self, name: str) -> _iam.Role:
        """create instance role"""
        functional_role_name = name + "FunctionalRole" + self.region
        instance_role = _iam.Role(self, functional_role_name,
                                  role_name=functional_role_name,
                                  assumed_by=_iam.ServicePrincipal('ec2.amazonaws.com')
                                  )

        instance_role.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        inst_policy_name = name + "InstanceProfilePolicy" + self.region
        inst_policy = \
            _iam.Policy(
                self, inst_policy_name,
                policy_name=inst_policy_name,
                statements=[
                    _iam.PolicyStatement(
                        effect=_iam.Effect.ALLOW,
                        sid="SSMPermissionsPolicyForSSMandCWAgent",
                        actions=[
                            "s3:GetObject"
                        ],
                        resources=[
                            "arn:aws:s3:::" + self.node.try_get_context("qs_s3_bucket") +
                            "-" + self.region + "/*",
                            "arn:aws:s3:::amazoncloudwatch-agent-" + self.region + "/*",
                            "arn:aws:s3:::aws-ssm-" + self.region + "/*",
                            "arn:aws:s3:::aws-windows-downloads-" + self.region + "/*",
                            "arn:aws:s3:::amazon-ssm-" + self.region + "/*",
                            "arn:aws:s3:::amazon-ssm-packages-" + self.region + "/*",
                            "arn:aws:s3:::" + self.region + "-birdwatcher-prod/*",
                            "arn:aws:s3:::aws-ssm-distributor-file-" + self.region + "/*",
                            "arn:aws:s3:::patch-baseline-snapshot-" + self.region + "/*"
                        ]),
                    _iam.PolicyStatement(
                        effect=_iam.Effect.ALLOW,
                        sid="CWAgentPermissions",
                        actions=[
                            "cloudwatch:PutMetricData",
                            "ec2:DescribeVolumes",
                            "ec2:DescribeTags",
                            "logs:PutLogEvents",
                            "logs:DescribeLogStreams",
                            "logs:DescribeLogGroups",
                            "logs:CreateLogStream",
                            "logs:CreateLogGroup"
                        ],
                        resources=[
                            "*"
                        ]),
                    _iam.PolicyStatement(
                        effect=_iam.Effect.ALLOW,
                        sid="SSMParameterStorePermissions",
                        actions=[
                            "ssm:GetParameter"
                        ],
                        resources=[
                            "arn:aws:ssm:*:*:parameter/AmazonCloudWatch-*"
                        ])
                ]
            )

        inst_policy.attach_to_role(instance_role)
        self._instance_role[name] = instance_role

        return instance_role

    def create_security_group(self, cid: str, name: str = "", description: str = "") \
            -> _ec2.SecurityGroup:
        """create security group"""
        if name == "":
            name = cid

        if description == "":
            description = f"Security Group {name}"

        self._security_groups[cid] = _ec2.SecurityGroup(self, cid,
                                                        vpc=self._vpc,
                                                        allow_all_outbound=False,
                                                        description=description,
                                                        security_group_name=name
                                                        )

        return self._security_groups[cid]

    # pylint: disable=too-many-arguments
    def add_security_group_rule(self, sg_id: str, protocol: _ec2.Protocol, cidr_range: str = None,
                                prefix_list: str = None,
                                from_port: int = 0,
                                to_port: int = 0, is_ingress: bool = True, description: str = None):
        """add security group rule"""
        if cidr_range is None:
            cidr_range = self._vpc.vpc_cidr_block

        if from_port != 0 and to_port == 0:
            to_port = from_port

        if prefix_list is not None:
            peer = _ec2.Peer.prefix_list(prefix_list)
            rule_id = f'{sg_id}_{protocol.name}_prefixlist_{from_port}_{to_port}'
        else:
            peer = _ec2.Peer.ipv4(cidr_range)
            rule_id = f'{sg_id}_{protocol.name}_{cidr_range}_{from_port}_{to_port}'

        if is_ingress:
            self._security_groups[sg_id].add_ingress_rule(
                peer=peer,
                connection=_ec2.Port(
                    string_representation=rule_id,
                    protocol=protocol,
                    from_port=from_port,
                    to_port=to_port
                ),
                description=description
            )
        else:
            self._security_groups[sg_id].add_egress_rule(
                peer=peer,
                connection=_ec2.Port(
                    string_representation=rule_id,
                    protocol=protocol,
                    from_port=from_port,
                    to_port=to_port
                ),
                description=description
            )

    def get_security_group_id(self, sg_id: str) -> str:
        """get security group id"""
        return self._security_groups[sg_id].security_group_id

    def get_security_group(self, sg_id: str) -> _ec2.SecurityGroup:
        """get security group"""
        return self._security_groups.get(sg_id)

    def create_nacl(self, cid: str, name: str, description: str,
                    subnet_selection: _ec2.SubnetSelection) -> None:
        """create nacl"""
        if name is None:
            name = cid

        if description == "":
            description = f"NACL {name}"

        self._nacls[cid] = _ec2.NetworkAcl(self, id=cid, vpc=self._vpc, network_acl_name=name,
                                           subnet_selection=subnet_selection)

    # pylint: disable=too-many-arguments
    def add_nacl_entry(self, cid: str, nacl_id: str, cidr: _ec2.AclCidr, rule_number: int,
                       traffic: _ec2.AclTraffic = _ec2.AclTraffic.all_traffic(),
                       direction: _ec2.TrafficDirection = _ec2.TrafficDirection.INGRESS,
                       network_acl_entry_name: str = "",
                       rule_action: _ec2.Action = _ec2.Action.ALLOW):
        """add nacl entry"""
        nacl: _ec2.NetworkAcl = self._nacls[cid]
        nacl.add_entry(id=nacl_id, cidr=cidr, rule_number=rule_number, traffic=traffic,
                       direction=direction, network_acl_entry_name=network_acl_entry_name,
                       rule_action=rule_action)
