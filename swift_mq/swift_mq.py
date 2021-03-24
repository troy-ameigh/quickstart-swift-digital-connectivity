"""Nested Stack for creating Amazon MQ"""
from aws_cdk import (
    core,
    aws_kms as _kms,
    aws_amazonmq as _mq,
    aws_secretsmanager as _secrets
)

from security.generic_security import GenericSecurity
from network.generic_network import GenericNetwork


class SwiftMQ(core.NestedStack):
    """Nested Stack for creating Amazon MQ"""
    # pylint: disable=too-many-arguments
    def __init__(self, scope: core.Construct, cid: str,
                 network: GenericNetwork,
                 security: GenericSecurity,
                 workload_key: _kms.Key,
                 **kwargs) -> None:
        super().__init__(scope, cid, **kwargs)

        mq_sg = security.create_security_group("MQSG")

        secret_name = cid + "Secret"
        sec = _secrets.Secret(self, secret_name, encryption_key=workload_key,
                              generate_secret_string=_secrets.SecretStringGenerator(
                                  exclude_characters="%+~`#$&*()|[]{}=:, ;<>?!'/@",
                                  password_length=20,
                                  secret_string_template="{\"username\":\"admin\"}",
                                  generate_string_key="password"))
        sec_cfn = sec.node.default_child
        sec_cfn.override_logical_id(secret_name)

        self._mq = _mq.CfnBroker(
            self, cid, auto_minor_version_upgrade=False, broker_name=cid,
            deployment_mode="ACTIVE_STANDBY_MULTI_AZ",
            logs=_mq.CfnBroker.LogListProperty(audit=True, general=True),
            encryption_options=
            _mq.CfnBroker.EncryptionOptionsProperty(use_aws_owned_key=False,
                                                    kms_key_id=workload_key.key_id),
            engine_type="ACTIVEMQ",
            engine_version="5.15.13",
            host_instance_type="mq.m5.large",
            publicly_accessible=False,
            subnet_ids=network.get_isolated_subnets("MQ").subnet_ids,
            security_groups=[mq_sg.security_group_id],
            users=[
                _mq.CfnBroker.UserProperty(
                    username=sec.secret_value_from_json("username").to_string(),
                    password=sec.secret_value_from_json("password").to_string())])

    def get_arn(self) -> str:
        """getting mq instance reference"""
        return self._mq.attr_arn
