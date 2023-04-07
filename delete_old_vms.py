# Delete old virtual machines for DRIVERS-2411 tests.
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
import datetime
import os

sub_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group_name = "DRIVERS-2411"
client = ComputeManagementClient(
    credential=DefaultAzureCredential(), subscription_id=sub_id)
cmclient = ComputeManagementClient(
    credential=DefaultAzureCredential(), subscription_id=sub_id)
nmclient = NetworkManagementClient(
    credential=DefaultAzureCredential(), subscription_id=sub_id)
vm_names = []
nic_names = []
ip_names = []
for vm in cmclient.virtual_machines.list(resource_group_name):
    try:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        delta = now - vm.time_created
        if delta < datetime.timedelta(hours=1):
            print("{} is less than 2 hours old. Age is: {} ... skipping".format(
                vm.name, delta))
            continue
        vm_names.append(vm.name)
        # Delete Network Interfaces before Virtual Machine.
        for nic_ref in vm.network_profile.network_interfaces:
            nic_name = nic_ref.id.split("/")[-1]
            nic_names.append(nic_name)
            nic = nmclient.network_interfaces.get(
                resource_group_name, nic_name)
            for ipconf in nic.ip_configurations:
                ip_name = ipconf.public_ip_address.id.split("/")[-1]
                ip_names.append(ip_name)
    except Exception as e:
        print("Exception occurred: {}".format(e))

print("Going to delete the following resources:")
print("Virtual Machines: {}".format(vm_names))
print("Network Interfaces: {}".format(nic_names))
print("IPs: {}".format(ip_names))

# Delete Virtual Machine and Network Interface before IP to avoid the error " In order to delete the public IP, disassociate/detach the Public IP address from the resource"
# print ("Press <enter> to proceed")
# import sys
# sys.stdin.readline()

for vm_name in vm_names:
    try:
        print("delete vm {} ... begin".format(vm_name))
        cmclient.virtual_machines.begin_delete(
            resource_group_name, vm_name).result()
        print("delete vm {} ... end".format(vm_name))
    except Exception as e:
        print("Exception occurred: {}".format(e))

for nic_name in nic_names:
    try:
        print("delete nic {} ... begin".format(nic_name))
        nmclient.network_interfaces.begin_delete(
            resource_group_name, nic_name).result()
        print("delete nic {} ... end".format(nic_name))
    except Exception as e:
        print("Exception occurred: {}".format(e))

for ip_name in ip_names:
    try:
        print("delete ip {} ... begin".format(ip_name))
        nmclient.public_ip_addresses.begin_delete(
            resource_group_name, ip_name).result()
        print("delete ip {} ... end".format(ip_name))
    except Exception as e:
        print("Exception occurred: {}".format(e))

# Also delete old NSGs.
for vm_name in vm_names:
    # NSG name is determined by create-vm.sh script in drivers-evergreen-tools
    nsg_name = vm_name + "-NSG"
    try:
        print("delete nsg {} ... begin".format(nsg_name))
        nmclient.network_security_groups.begin_delete(
            resource_group_name, nsg_name).result()
        print("delete nsg {} ... end".format(nsg_name))
    except Exception as e:
        print("Exception occurred: {}".format(e))
