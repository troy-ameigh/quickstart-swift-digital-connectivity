"""Nested Stack for RDS Oracle database used for AMH"""
from aws_cdk import (
    core,
    aws_kms as _kms,
    aws_rds as _rds,
    aws_ec2 as _ec2
)

from security.generic_security import GenericSecurity
from network.generic_network import GenericNetwork


class SwiftDatabase(core.NestedStack):
    """Nested Stack for RDS Oracle database used for AMH"""
    # pylint: disable=too-many-arguments
    def __init__(self, scope: core.Construct, cid: str,
                 network: GenericNetwork,
                 security: GenericSecurity,
                 workload_key: _kms.Key,
                 **kwargs) -> None:
        super().__init__(scope, cid, **kwargs)

        rds_sg = security.create_security_group("RDSSG")
        self._oracle_rds = None
        if not self.node.try_get_context("skip_oracle") == "true":
            resource_name = "AMHRDSOracleInstance"
            self._oracle_rds = _rds.DatabaseInstance(
                self, resource_name, engine=_rds.DatabaseInstanceEngine.oracle_ee(
                    version=_rds.OracleEngineVersion.VER_12_2_0_1_2020_07_R1),
                vpc=network.get_vpc(),
                multi_az=True, storage_encryption_key=workload_key,
                security_groups=[rds_sg],
                cloudwatch_logs_exports=['trace',
                                         'audit',
                                         'alert',
                                         'listener'],
                vpc_subnets=_ec2.SubnetSelection(subnet_name="Database"))

    def get_db_instance(self) -> _rds.DatabaseInstance:
        """get reference of the database instance"""
        return self._oracle_rds
