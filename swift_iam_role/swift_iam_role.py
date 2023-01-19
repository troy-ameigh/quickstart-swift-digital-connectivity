"""Nested Stack for the sample IAM Role creation for Managing SWIFT components"""
from typing import List

from aws_cdk import (
    aws_rds as _rds,
    aws_iam as _iam
)
from constructs import Construct
from aws_cdk import NestedStack

class SwiftIAMRole(NestedStack):
    """Nested Stack for the sample IAM Role creation for Managing SWIFT components"""

    # pylint: disable=too-many-arguments
    def __init__(self, scope: Construct, cid: str, instance_ids: List[str], mq_broker_arn: str,
                 database_instance: _rds.DatabaseInstance, **kwargs):
        super().__init__(scope, cid, **kwargs)

        self.create_swift_instance_operator_role(instance_ids)

        self.create_swift_infrastructure_role(
            database_instance=database_instance, instance_ids=instance_ids,
            mq_broker_arn=mq_broker_arn)

    def create_swift_instance_operator_role(self, instance_ids):
        """create swift instance operator role"""
        swift_instance_operator_role = \
            _iam.Role(self, "SWIFTInstanceOperatorRole",
                      role_name="SWIFTInstanceOperatorRole",
                      assumed_by=_iam.AccountPrincipal(account_id=self.account)
                      .with_conditions({"Bool": {"aws:MultiFactorAuthPresent": "true"}})
                      )

        instances_resource = []
        if instance_ids is not None:
            for instance_id in instance_ids:
                instances_resource.append(
                    "arn:aws:ec2:" + self.region + ":" + self.account + ":instance/" + instance_id)

        ssm_doc_resource = "arn:aws:ssm:" + self.region + \
                           ":" + self.account + ":document/SSM-SessionManagerRunShell"

        statements = [
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW, actions=["ssm:StartSession", "ssm:SendCommand"],
                resources=[ssm_doc_resource] + instances_resource,
                conditions={"BoolIfExists": {
                    "ssm:SessionDocumentAccessCheck": "true"}}),
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["ssm:DescribeSessions", "ssm:GetConnectionStatus",
                         "ssm:DescribeInstanceInformation",
                         "ssm:DescribeInstanceProperties", "ec2:DescribeInstances"],
                resources=["*"]),
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["ssm:TerminateSession"],
                resources=[
                    "arn:aws:ssm:*:*:session/${aws:username}-*"])]
        _iam.Policy(
            self, "SSMInstanceAccessPolicy", policy_name="SSMInstanceAccessPolicy",
            roles=[swift_instance_operator_role], statements=statements,
            force=True)

    def create_swift_infrastructure_role(
            self, database_instance: _rds.DatabaseInstance, instance_ids: List[str],
            mq_broker_arn: str):
        """create swift infrastructure role"""
        swift_infrastructure_role = \
            _iam.Role(self, "SWIFTInfrastructureRole",
                      role_name="SWIFTInfrastructureRole",
                      assumed_by=_iam.AccountPrincipal(account_id=self.account)
                      .with_conditions({"Bool": {"aws:MultiFactorAuthPresent": "true"}})
                      )
        instances_resource = []
        if instance_ids is not None:
            for instance_id in instance_ids:
                instances_resource.append(
                    "arn:aws:ec2:" + self.region + ":" + self.account + ":instance/" + instance_id)
        statements = [
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW, actions=["rds:Describe*"],
                resources=["*"]),
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW, actions=["rds:Start*", "rds:Stop*"],
                resources=[database_instance.instance_arn]),
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW, actions=["ec2:Describe*"],
                resources=["*"]),
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW, actions=["ec2:Start*", "ec2:Stop*"],
                resources=instances_resource),
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW, actions=["mq:List*", "mq:Describe*", "mq:RebootBroker"],
                resources=[mq_broker_arn]),
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW, actions=["logs:List*", "logs:Describe*", "logs:Get*"],
                resources=["*"])]

        _iam.Policy(
            self, "SwiftInfrastructurePolicy", policy_name="SwiftInfrastructurePolicy",
            roles=[swift_infrastructure_role], statements=statements,
            force=True)
