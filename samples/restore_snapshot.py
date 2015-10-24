# Copyright 2015 Michael Rice <michael@michaelrice.org>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import print_function

import atexit

import requests

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from tools import cli
from tools import pchelper

requests.packages.urllib3.disable_warnings()


def setup_args():
    parser = cli.build_arg_parser()
    # parser.add_argument('-j', '--uuid', required=False,
    #                     help="UUID of the VirtualMachine you want to find."
    #                          " If -i is not used BIOS UUID assumed.")
    # parser.add_argument('-i', '--instance', required=False,
    #                     action='store_true',
    #                     help="Flag to indicate the UUID is an instance UUID")
    parser.add_argument('-n', '--name', 
                        required=False,
                        action='store',
                        help="name of VirtualMachine")
    my_args = parser.parse_args()
    return cli.prompt_for_password(my_args)


args = setup_args()
si = None
instance_search = False
try:
    si = SmartConnect(host=args.host,
                      user=args.user,
                      pwd=args.password,
                      port=int(args.port))
    atexit.register(Disconnect, si)
except IOError:
    pass


if not si:
    raise SystemExit("Unable to connect to host with supplied info.")


def get_all_vms(virtual_machine, depth=1):
   
    maxdepth = 10

    # if this is a group it will have children. if it does, recurse into them
    # and then return
    if hasattr(virtual_machine, 'childEntity'):
        if depth > maxdepth:
            return []
        vmList = virtual_machine.childEntity
        vms = []
        for c in vmList:
            vms.extend(get_all_vms(c, depth + 1))
        return vms
    return [virtual_machine]

targetVm = None

if args.name:
    vms = []
    content = si.RetrieveContent()   
    children = content.rootFolder.childEntity
    for child in children:
        if hasattr(child, 'vmFolder'):
            datacenter = child
        else:
            # some other non-datacenter type object
            continue

        vm_folder = datacenter.vmFolder
        vm_list = vm_folder.childEntity
        for vm in vm_list:
            vms.extend(get_all_vms(vm, 10))
    for vm in vms:        
        summary = vm.summary
        name = summary.config.name
        if (name == args.name):
            targetVm = vm

if targetVm is None:
    raise SystemExit("Unable to locate VirtualMachine.")

print(targetVm.summary.config.name)


#desc = None
#if args.description:
#    desc = args.description

task = targetVm.RevertToCurrentSnapshot_Task()
print(task.info)
print("Restore Completed.")
# del vm
# vm = si.content.searchIndex.FindByUuid(None, args.uuid, True, instance_search)
# snap_info = vm.snapshot

# tree = snap_info.rootSnapshotList
# while tree[0].childSnapshotList is not None:
#     print("Snap: {0} => {1}".format(tree[0].name, tree[0].description))
#     if len(tree[0].childSnapshotList) < 1:
#         break
#     tree = tree[0].childSnapshotList
