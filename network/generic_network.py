"""Nested Stack for Networking"""
from aws_cdk import (
    core,
    aws_ec2 as _ec2
)


class GenericNetwork(core.NestedStack):
    """Nested Stack for Networking"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, scope: core.Construct, cid: str,
                 cidr_range: str = "10.10.0.0/16", **kwargs) -> None:
        super().__init__(scope, cid, **kwargs)
        self._is_generated: bool = False
        self._subnet_configuration: [_ec2.SubnetConfiguration] = []
        self._cidr_range = cidr_range
        self._base_vpc: _ec2.Vpc
        self._vgw_propagation_subnet: _ec2.SubnetSelection
        self._has_private_subnet = False
        self._max_azs = 2
        self._vgw = False

    def generate(self):
        """Generate networking stack (VPC) with all the variable set in this instance """
        self._is_generated = True
        nat_gateways = 0
        if self._has_private_subnet:
            nat_gateways = self._max_azs

        self._base_vpc = _ec2.Vpc(self, "SwiftVPC",
                                  cidr=self._cidr_range,
                                  enable_dns_hostnames=True,
                                  enable_dns_support=True,
                                  subnet_configuration=self._subnet_configuration,
                                  max_azs=self._max_azs,
                                  nat_gateways=nat_gateways,
                                  vpn_gateway=self._vgw,
                                  vpn_route_propagation=[self._vgw_propagation_subnet]
                                  )

        for i in range(self._max_azs):
            selected_subnet: _ec2.SelectedSubnets = self._base_vpc.select_subnets(
                availability_zones=[self.availability_zones[i]])
            for subnet in selected_subnet.subnets:
                subnet_cfn = subnet.node.default_child
                subnet_cfn.add_property_override("AvailabilityZone",
                                                 {"Fn::Select": [str(i), {"Fn::GetAZs": ""}]})

    def set_vgw_propagation_subnet(self, subnet_selection: _ec2.SubnetSelection):
        """setting subnets for vgw propagation"""
        self._vgw_propagation_subnet = subnet_selection

    def set_max_azs(self, m_val: int = 2):
        """setting the AZ numbers"""
        self._max_azs = m_val

    def set_vgw(self, vgw: bool) -> None:
        """setting for vgw creation"""
        self._vgw = vgw

    def add_private_subnets(self, name: str) -> None:
        """adding private subnet, Public Subnet and
        Nat Gateway will be created and needed for this"""
        self._subnet_configuration.append(
            _ec2.SubnetConfiguration(
                name=name,
                subnet_type=_ec2.SubnetType.PRIVATE,
                cidr_mask=24,
                reserved=False
            )
        )
        self._has_private_subnet = True

    def add_isolated_subnets(self, name: str) -> None:
        """adding isolated subnet, air gap"""
        self._subnet_configuration.append(
            _ec2.SubnetConfiguration(
                name=name,
                subnet_type=_ec2.SubnetType.ISOLATED,
                cidr_mask=24,
                reserved=False
            )
        )

    def add_public_subnets(self, name: str) -> None:
        """adding public subnets"""
        self._subnet_configuration.append(
            _ec2.SubnetConfiguration(
                name=name,
                subnet_type=_ec2.SubnetType.PUBLIC,
                cidr_mask=24,
                reserved=False
            )
        )

    def _get_subnets(self, subnet_type: _ec2.SubnetType, group_name: str = "") \
            -> _ec2.SelectedSubnets:
        """private helper method of selecting subnet """
        if group_name == "":
            return self._base_vpc.select_subnets(
                subnet_type=subnet_type
            )

        return self._base_vpc.select_subnets(
            subnet_group_name=group_name
        )

    def get_private_subnets(self, subnet_group_name: str = "") -> _ec2.SelectedSubnets:
        """getting private subnets by subnet group name"""
        if self._is_generated:
            return self._get_subnets(_ec2.SubnetType.PRIVATE, subnet_group_name)

        raise NotGeneratedException("Please call stack.generate() first")

    def get_isolated_subnets(self, subnet_group_name: str = "") -> _ec2.SelectedSubnets:
        """getting isolated subnets by group name"""
        if self._is_generated:
            return self._get_subnets(_ec2.SubnetType.ISOLATED, subnet_group_name)
        raise NotGeneratedException("Please call stack.generate() first")

    def get_public_subnets(self, subnet_group_name: str = "") -> _ec2.SelectedSubnets:
        """getting public subnets"""
        if self._is_generated:
            return self._get_subnets(_ec2.SubnetType.PUBLIC, subnet_group_name)
        raise NotGeneratedException("Please call stack.generate() first")

    def get_vpc(self) -> _ec2.Vpc:
        """getting vpc reference"""
        return self._base_vpc


class NotGeneratedException(Exception):
    """Exception for calling methods before generation"""
