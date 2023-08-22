# Delete old virtual machines for DRIVERS-2411 tests.
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
import os
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

sub_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group_name = "DRIVERS-2411"
client = ComputeManagementClient(
    credential=DefaultAzureCredential(), subscription_id=sub_id)
cmclient = ComputeManagementClient(
    credential=DefaultAzureCredential(), subscription_id=sub_id)
nmclient = NetworkManagementClient(
    credential=DefaultAzureCredential(), subscription_id=sub_id)
all_vm_names = []  # Example value: `vmname-RUBY-10561`
orphan_nic_names = []  # Example value: `vmname-RUBY-10561VMNic`
orphan_ip_names = []  # Example value: `vmname-RUBY-10561-PUBLIC-IP`
# Example value: `vmname-RUBY-10561-NSG` or `vmname-RUBY-10561NSG`.
orphan_nsg_names = []

for vm in cmclient.virtual_machines.list(resource_group_name):
    all_vm_names.append(vm.name)

# Get orphaned NICs.
for nic in nmclient.network_interfaces.list(resource_group_name):
    is_orphan = True
    for vm_name in all_vm_names:
        if vm_name + "VMNic" == nic.name:
            is_orphan = False
            break
    if is_orphan:
        orphan_nic_names.append(nic.name)

# Get orphaned IPs.
for ip in nmclient.public_ip_addresses.list(resource_group_name):
    is_orphan = True
    for vm_name in all_vm_names:
        if vm_name + "-PUBLIC-IP" == ip.name:
            is_orphan = False
            break
    if is_orphan:
        orphan_ip_names.append(ip.name)

# Get orphaned NSGs.
for nsg in nmclient.network_security_groups.list(resource_group_name):
    is_orphan = True
    for vm_name in all_vm_names:
        if vm_name + "-NSG" == nsg.name or vm_name + "NSG" == nsg.name:
            is_orphan = False
            break
    if is_orphan:
        orphan_nsg_names.append(nsg.name)

print("Going to delete the following resources:")
print("Network Interfaces: {}".format(orphan_nic_names))
print("IPs: {}".format(orphan_ip_names))
print("NSGs: {}".format(orphan_nsg_names))
if args.dry_run:
    print("dry run detected. Not deleting")
    sys.exit(1)


for nic_name in orphan_nic_names:
    try:
        print("delete orphan nic {} ... begin".format(nic_name))
        nmclient.network_interfaces.begin_delete(
            resource_group_name, nic_name).result()
        print("delete orphan nic {} ... end".format(nic_name))
    except Exception as e:
        print("Exception occurred: {}".format(e))

for ip_name in orphan_ip_names:
    try:
        print("delete orphan ip {} ... begin".format(ip_name))
        nmclient.public_ip_addresses.begin_delete(
            resource_group_name, ip_name).result()
        print("delete orphan ip {} ... end".format(ip_name))
    except Exception as e:
        print("Exception occurred: {}".format(e))

# Also delete old NSGs.
for nsg_name in orphan_nsg_names:
    try:
        print("delete orphan nsg {} ... begin".format(nsg_name))
        nmclient.network_security_groups.begin_delete(
            resource_group_name, nsg_name).result()
        print("delete orphan nsg {} ... end".format(nsg_name))
    except Exception as e:
        print("Exception occurred: {}".format(e))
