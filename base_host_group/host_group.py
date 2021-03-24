"""Base class for EC2 instance"""
from aws_cdk import (
    core,
    aws_ec2 as _ec2,
    aws_kms as _kms,
)
from aws_cdk.core import Aws
from cdk_ec2_key_pair import KeyPair

from network.generic_network import GenericNetwork
from security.generic_security import GenericSecurity


class HostGroup(core.NestedStack):
    """Base class for EC2 instance"""

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    def __init__(self, scope: core.Construct, cid: str,
                 component: str,
                 network: GenericNetwork,
                 security: GenericSecurity,
                 workload_key: _kms.Key,
                 ops_key: KeyPair = None,
                 vpc_subnets: _ec2.SubnetSelection = None,
                 ami_id: str = None,
                 private_ip: str = None,
                 **kwargs):
        super().__init__(scope, cid, **kwargs)

        self.instance_id = ""
        self._workload_key = workload_key
        sec_group = security.get_security_group(component + "SG")
        if not sec_group:
            sec_group = security.create_security_group(component + "SG")
            endpt_sg = security.get_security_group("VPCEndpointSG")
            endpt_sg.connections.allow_from(
                sec_group,
                port_range=_ec2.Port(
                    protocol=_ec2.Protocol.TCP,
                    string_representation=component + " -> Endpoint (443)",
                    from_port=443,
                    to_port=443
                ),
                description="VPC Endpoint Ingress rule from " + component
            )
            sec_group.connections.allow_to(
                endpt_sg,
                port_range=_ec2.Port(
                    protocol=_ec2.Protocol.TCP,
                    string_representation=component + " -> Endpoint (443)",
                    from_port=443,
                    to_port=443
                ),
                description="Egress rule to VPC Endpoint for " + component

            )

        instance_type = _ec2.InstanceType.of(instance_class=_ec2.InstanceClass.STANDARD5,
                                             instance_size=_ec2.InstanceSize.XLARGE)
        key_name = None
        if ops_key is not None:
            key_name = ops_key.key_pair_name

        if vpc_subnets is None:
            vpc_subnets = _ec2.SubnetSelection(subnet_group_name=component)

        user_data = None
        if ami_id is None:
            machine_image = _ec2.MachineImage.lookup(
                name="RHEL-8.3.0_HVM-????????-x86_64-0-Hourly2-GP2", owners=["309956199498"])
            user_data = _ec2.UserData.for_linux()
            for line in get_user_data(self.region, self.node.try_get_context("qs_s3_bucket")):
                user_data.add_commands(line)
        else:
            machine_image = _ec2.MachineImage.lookup(name="*", filters={"image-id": [ami_id]})

        instance_role = security.get_instance_role(component)
        if not instance_role:
            instance_role = security.create_instance_role(component)

        # noinspection PyTypeChecker
        self.instance = _ec2.Instance(self, cid, instance_type=instance_type,
                                      machine_image=machine_image,
                                      block_devices=[_ec2.BlockDevice(
                                          device_name="/dev/sda1",
                                          volume=_ec2.BlockDeviceVolume.ebs(
                                              volume_size=100, encrypted=True))],
                                      vpc=network.get_vpc(),
                                      role=instance_role, security_group=sec_group,
                                      vpc_subnets=vpc_subnets, key_name=key_name,
                                      private_ip_address=private_ip, user_data=user_data)
        self.instance_id = self.instance.instance_id

    def get_instance_id(self) -> str:
        """get instance id as string"""
        return self.instance_id

    def get_instance(self) -> _ec2.Instance:
        """get instance reference"""
        return self.instance


def get_user_data(region: str, bucket_name: str):
    """User data for the ec2"""
    return [
        "sleep 120",
        "dnf config-manager --disable rhui-client-config-server-8",
        "dnf config-manager --disable rhel-8-appstream-rhui-rpms",
        "dnf config-manager --disable rhel-8-baseos-rhui-rpms",
        "dnf install -y https://s3." + region + "." + Aws.URL_SUFFIX + "/" +
        "amazon-ssm-" + region + "/latest/linux_amd64/amazon-ssm-agent.rpm",
        "systemctl enable amazon-ssm-agent",
        "systemctl start amazon-ssm-agent",
        "curl https://s3." + region + "." + Aws.URL_SUFFIX + "/amazoncloudwatch-agent-" + region +
        "/redhat/amd64/latest/amazon-cloudwatch-agent.rpm -o /tmp/amazon-cloudwatch-agent.rpm",
        "rpm -U /tmp/amazon-cloudwatch-agent.rpm",
        "curl https://" + bucket_name + "-" + region + ".s3." + region +
        "." + Aws.URL_SUFFIX + "/" +
        "quickstart-swift-digital-connectivity/assets/cw_agent_config.json -o /tmp/cw_agent_config.json",
        "/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl"
        " -a fetch-config -m ec2 -s -c file:/tmp/cw_agent_config.json"
    ]
