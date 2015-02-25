# vmfusion-python

vmfusion-python is a low-level python interface for the VMware Fusion command
line tools vmrun and vmware-vdiskmanager. It aims to be human readable (because
I still have no idea why -k is shrink, -n is rename and -r is convert) and
easy to use.

The vmrun command comes with a ton of command line options. At the moment, only
the common commands are implemented because I have yet to find an actual use
case for the rest. If you have need for a non-implemented command, open an issue
or send me a pull request.

# Installation

    $ pip install vmfusion

# Overview

## vmrun

The `vmrun` tool can be used to control the runtime state of a VM.

Note: Contrary to the behavior of vmrun, the API will work with both absolute
_and_ relative VMX paths.

### list

Return information about all running VMs.

Usage: `vmrun.list()`

Example:

    >>> from vmfusion import vmrun
    >>> print vmrun.list()
    {
        'count': 3,
        'machines': [
        '/Users/msteinhoff/Documents/Virtual Machines/test1/test1.vmx',
        '/Users/msteinhoff/Documents/Virtual Machines/test1/test2.vmx', 
        '/Users/Shared/Virtual Machines/test3/test3.vmx',
        ]
    }

*Note:* This will only return actual running VMs and is not the same als the
Virtual Machine Library from the VMware Fusion GUI, which also displays halted
and suspended VMs.

### start

Power on a VM.

Usage:

    vmrun.start( vmx )

**Note/Warning:** There is an optional `gui` parameter which can be set to False
to launch the VM in *nogui mode*.

The nogui mode is weird. In nogui mode, the VM window will not be visible but
displayed in VMware Fusion.app when its already running. If the Fusion GUI is
not running and you launch it or close/launch it, the VM gets converted back to
gui mode. Oh and if you then close VMware Fusion.app the VM gets suspended. (at
least thats whats happening on my system).

### stop

Shutdown a VM.

Usage:

    vmrun.stop( vmx, soft=True )

When `soft` is set to True (default), configured shutdown scripts will be
executed and an shutdown signal will be sent to the guest OS. For this to work,
vmware tools need to be installed. Otherwise, the VM is killed with no mercy.

### reset

Reboot a VM.

Usage:

    vmrun.reset( vmx, soft=True )

When `soft` is set to True (default), configured shutdown/power-on scripts will
be executed and an shutdown signal will be sent to the guest OS. For this to
work, vmware tools need to be installed. Otherwise, the VM is killed with no
mercy.

### suspend

Suspend VM state to disk.

Usage:

    vmrun.suspend( vmx, soft=True )

When `soft` is set to True (default), configured suspend scripts will be
executed before the system is suspended.

### pause

Halt the CPU execution of a VM.

Usage:

    vmrun.pause( vmx )

### revertToSnapshot

Set the virtual machine state to a snapshot.

Usage:

    vmrun.revertToSnapshot( vmx, snapshot_name )


### unpause

Continue CPU execution of a VM.

Usage:

    vmrun.unpause( vmx )

## vdiskmanager

With the `vdiskmanager` tool VMDK disks can be managed. For all methods, the `vmdk` parameter always expects a relative path to the vmdk file.

### create

Creates a new VMDK file with the given parameters.

Usage: 

    vdiskmanager.create( vmdk, size, disk_type=None, adapter_type=None )

Arguments:

- `size`
    
    A size specification readable by the tool, e.g. `100MB`, `20GB`, `1TB`. No
    validation is performed.

- `disk_type`

    Optional type of the disk to be created, one of the following:

    - `SPARSE_SINGLE`: A single growable VMDK file
    - `SPARSE_SPLIT`: Many growable VMDK files, split into 2 GB slices
    - `PREALLOC_SINGLE`: A single preallocated VMDK file
    - `PREALLOC_SPLIT`: Many preallocated 2 GB VMDK files

    Default is `SPARSE_SPLIT`.

- `adapter_type`

    Optional type of the disk adapter, one of the following:

    - `IDE`
    - `LSILOGIC`
    - `BUSLOGIC`

    Default is `LSILOGIC`.

### defragment

Defragments VMDK files on the VMware level (not to be confused with guest
filesystem defagmentation).

Usage: 
    
    vdiskmanager.defragment( vmdk )

### shrink

This will perform a shrink of the VMDK on the VMware level (The guest
filesystem must be prepared for this to work, e.g. with the zerofill tool on
Linux.).

Usage:

    vdiskmanager.shrink( vmdk )

### rename

This will rename a VMDK file. Useful for large split disks with over 9000 2GB
slices.

Usage:

    vdiskmanager.rename( source_vmdk, destination_vmdk )

### convert

This will convert the disk type of the given VMDK file.

Usage:

    vdiskmanager.convert( vmdk, disk_type )

The `disk_type` parameter is the same as in create() and must be one of the
following:

- `SPARSE_SINGLE`: A single growable VMDK file
- `SPARSE_SPLIT`: Many growable VMDK files, split into 2 GB slices
- `PREALLOC_SINGLE`: A single preallocated VMDK file
- `PREALLOC_SPLIT`: Many preallocated 2 GB VMDK files

### expand

This will expand the VMDK to the given size.

Usage:

    vdiskmanager.convert( vmdk, new_size )

The `new_size` parameter must be a size specification readable by the tool, e.g.
`100MB`, `20GB`, `1TB`. No validation is performed.

# vmnet_*

It is often handy to gather certain information about the local VMware networks.

By default VMware creates a host-only network and a NAT network. Those are
represented by `vmnet_hostonly` and `vmnet_nat`. 

To retrieve the vnet-name (e.g. useful in VMX config files), use the following:

    >>> from vmfusion import vmnet_nat
    >>> print vmnet_nat.name
    vmnet8

There is a DHCP server running on both networks. To access the lease information,
use the following:

    >>> from vmfusion import vmnet_nat
    >>> print vmnet_nat.leases
    {
        '00:50:56:00:23:40': '192.168.128.130'
        '00:50:56:00:19:12': '192.168.128.129'
        '00:50:56:00:46:93': '192.168.128.136'
    }

The dhcp server stores lease information in a file on disk. The data in the
leases dictionary is read-only and not automatically updated. To reload the
latest data from the file, use the `reload()` method:

    vmnet_nat.leases.reload()

# Custom tool locations

The `vmrun` and `vdiskmanager` use the default location at `/Applications/VMware Fusion.app`. This can be changed by instantiating a custom _cli object.

vmrun at a custom location:

    >>> from vmfusion import vmrun_cli
    >>> vmrun_custom = vmrun_cli( '/Volumes/External/Applications/VMware Fusion.app'  )

Same goes with vdiskmanager:

    >>> from vmfusion import vdiskmanager_cli
    >>> vdiskmanager_custom = vdiskmanager_cli( '/Volumes/External/Applications/VMware Fusion.app'  )
    
To create a custom vmnet, use `vnet_cli`:

    >>> from vmfusion import vnet_cli
    >>> vmnet_custom = vnet_cli( 'vmnet6' )
    >>> print vmnet_custom.name
    vmnet6

# Contribution

Fork, code, pull request :)


# License

See LICENSE.txt
