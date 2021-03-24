"""Nested Stack to create the CMK for the entire SWIFT Connectivity workload"""
from aws_cdk import (
    core,
    aws_kms as _kms
)


class GenericCMK(core.NestedStack):
    """Nested Stack to create the CMK for the entire SWIFT Connectivity workload"""

    def __init__(self, scope: core.Construct, cid: str, **kwargs) -> None:
        super().__init__(scope, id=cid, **kwargs)

        key_name = "SwiftConnectivityCMK"
        self._cmk = _kms.Key(self, key_name,
                             alias=key_name,
                             description="Swift Connectivity CMK for use for all resources",
                             enabled=True,
                             enable_key_rotation=True,
                             removal_policy=core.RemovalPolicy.DESTROY
                             )

    def get_cmk(self) -> _kms.Key:
        """getter for cmk"""
        return self._cmk
