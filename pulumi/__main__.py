"""An Azure RM Python Pulumi program"""

from pulumi_azure_native import compute, network, resources

import pulumi

rg = resources.ResourceGroup("rg-test-squid", location="japaneast")
vnet = network.VirtualNetwork(
    "vnet-test-squid",
    resource_group_name=rg.name,
    location=rg.location,
    address_space=network.AddressSpaceArgs(
        address_prefixes=["10.0.0.0/16"],
    ),
)
nsg_proxy = network.NetworkSecurityGroup(
    "nsg-proxy",
    resource_group_name=rg.name,
    location=rg.location,
    security_rules=[
        # Inbound
        network.SecurityRuleArgs(
            name="AllowSquidInbound",
            access="Allow",
            direction="Inbound",
            protocol="Tcp",
            source_address_prefix="*",
            source_port_range="*",
            destination_address_prefix="*",
            destination_port_range="3128",
            priority=100,
            description="Allow squid inbound",
        ),
        network.SecurityRuleArgs(
            name="ssh",
            access="Allow",
            direction="Inbound",
            protocol="Tcp",
            source_address_prefix="*",
            source_port_range="*",
            destination_address_prefix="*",
            destination_port_range="22",
            priority=110,
            description="Allow SSH",
        ),
        # Outbound
        network.SecurityRuleArgs(
            name="AllowInternetOutbound",
            access="Allow",
            direction="Outbound",
            protocol="*",
            source_address_prefix="*",
            source_port_range="*",
            destination_address_prefix="Internet",
            destination_port_range="*",
            priority=200,
            description="Allow internet outbound",
        ),
    ],
)
nsg_vm = network.NetworkSecurityGroup(
    "nsg-vm",
    resource_group_name=rg.name,
    location=rg.location,
    security_rules=[
        # Inbound
        network.SecurityRuleArgs(
            name="ssh",
            access="Allow",
            direction="Inbound",
            protocol="Tcp",
            source_address_prefix="*",
            source_port_range="*",
            destination_address_prefix="*",
            destination_port_range="22",
            priority=100,
            description="Allow SSH",
        ),
        # Outbound
        network.SecurityRuleArgs(
            name="allow-proxy-outbound",
            access="Allow",
            direction="Outbound",
            protocol="*",
            source_address_prefix="*",
            source_port_range="*",
            destination_address_prefix="10.0.0.0/24",
            destination_port_range="3128",
            priority=3000,
            description="Allow proxy",
        ),
        network.SecurityRuleArgs(
            name="deny-outbound",
            access="Deny",
            direction="Outbound",
            protocol="*",
            source_address_prefix="*",
            source_port_range="*",
            destination_address_prefix="*",
            destination_port_range="*",
            priority=4000,
            description="Deny all outbound",
        ),
    ],
)

subnet_vm = network.Subnet(
    "subnet-vm",
    resource_group_name=rg.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.1.0/24",
    network_security_group={
        "id": nsg_vm.id,
    },
)
subnet_proxy = network.Subnet(
    "subnet-proxy",
    resource_group_name=rg.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.0.0/24",
    network_security_group={
        "id": nsg_proxy.id,
    },
)

# --------------------------- SSH vm --------------------------

# Create a network interface
network_interface = network.NetworkInterface(
    "nic-vm",
    resource_group_name=rg.name,
    location=rg.location,
    ip_configurations=[
        network.NetworkInterfaceIPConfigurationArgs(
            name="IpConfig",
            subnet=network.SubnetArgs(
                id=subnet_proxy.id,
            ),
            private_ip_allocation_method=network.IPAllocationMethod.DYNAMIC,
        ),
    ],
)

# Create a storage profile for the VM with an OS Disk
storage_profile = compute.OSDiskArgs(
    create_option="FromImage",
    name="osDiskSshHost",
    managed_disk=compute.ManagedDiskParametersArgs(
        storage_account_type="Premium_LRS",
    ),
    disk_size_gb=30,
)

# Define the virtual machine
vm = compute.VirtualMachine(
    "vm-ssh-host",
    resource_group_name=rg.name,
    location=rg.location,
    network_profile=compute.NetworkProfileArgs(
        network_interfaces=[
            compute.NetworkInterfaceReferenceArgs(id=network_interface.id, primary=True)
        ]
    ),
    hardware_profile=compute.HardwareProfileArgs(vm_size="Standard_B2ts_v2"),
    storage_profile=compute.StorageProfileArgs(
        os_disk=storage_profile,
        image_reference=compute.ImageReferenceArgs(
            publisher="Canonical",
            offer="0001-com-ubuntu-server-jammy",
            sku="22_04-lts",
            version="latest",
        ),
    ),
    os_profile=compute.OSProfileArgs(
        computer_name="vm-ssh-host",
        admin_username="admina",
        admin_password="09j!Bufdsb801222",
    ),
    priority="Spot",
)

# --------------------------- Proxy vm --------------------------


# Create a public IP address
public_ip = network.PublicIPAddress(
    "public-ip-proxy",
    resource_group_name=rg.name,
    location=rg.location,
    public_ip_allocation_method=network.IPAllocationMethod.STATIC,
)

# Create a network interface
network_interface = network.NetworkInterface(
    "nic-proxy",
    resource_group_name=rg.name,
    location=rg.location,
    ip_configurations=[
        network.NetworkInterfaceIPConfigurationArgs(
            name="IpConfig",
            subnet=network.SubnetArgs(
                id=subnet_proxy.id,
            ),
            public_ip_address=network.PublicIPAddressArgs(
                id=public_ip.id,
            ),
        ),
    ],
)

# Create a storage profile for the VM with an OS Disk
storage_profile = compute.OSDiskArgs(
    create_option="FromImage",
    name="osDisk",
    managed_disk=compute.ManagedDiskParametersArgs(
        storage_account_type="Premium_LRS",
    ),
    disk_size_gb=30,
)

# Define the virtual machine
vm = compute.VirtualMachine(
    "vm-proxy",
    resource_group_name=rg.name,
    location=rg.location,
    network_profile=compute.NetworkProfileArgs(
        network_interfaces=[
            compute.NetworkInterfaceReferenceArgs(id=network_interface.id, primary=True)
        ]
    ),
    hardware_profile=compute.HardwareProfileArgs(vm_size="Standard_A1_v2"),
    storage_profile=compute.StorageProfileArgs(
        os_disk=storage_profile,
        image_reference=compute.ImageReferenceArgs(
            publisher="Canonical",
            offer="0001-com-ubuntu-server-jammy",
            sku="22_04-lts",
            version="latest",
        ),
    ),
    os_profile=compute.OSProfileArgs(
        computer_name="vm-proxy",
        admin_username="admina",
        admin_password="09j!Bufdsb801222",
    ),
    priority="Spot",
)
