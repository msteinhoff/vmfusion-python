import os
import subprocess
from datetime import datetime, timedelta
from pyparsing import *

def file_must_exist( type, file ):
    if not os.path.isfile( file ):
        raise ValueError( "{0} at path {1} does not exist".format( type, file ) )

def file_must_not_exist( type, file ):
    if os.path.isfile( file ):
        raise ValueError( "{0} at path {1} already exists".format( type, file ) )

def get_abspath( path ):
    if not os.path.isabs( path ):
        path = os.path.abspath( path )

    return path

class vmrun_cli( object ):
    """Human readable python interface to the vmrun cli tool of VMware Fusion.

    Tested with VMware Fusion 5."""

    def __init__( self, bundle_directory=None ):
        if not bundle_directory:
            bundle_directory = '/Applications/VMware Fusion.app'

        vmrun = os.path.join( bundle_directory, 'Contents/Library/vmrun' )

        if not os.path.isfile( vmrun ):
            raise ValueError( "vmrun tool not found at path {0}".format( vmrun ) )

        self.tool_path = vmrun

    def __vmrun( self, command ):
        base = [ self.tool_path, '-T', 'fusion' ]
        base.extend( command )
        
        proc = subprocess.Popen( base, stdout=subprocess.PIPE )
        stdout = proc.stdout.readlines()

        return stdout

    def list( self ):
        output = self.__vmrun( [ 'list' ] )

        # Expected output:
        # Total running VMs: N
        # [optional absolute path to VMX 1]
        # [optional absolute path to VMX 2]
        # [optional absolute path to VMX n]
        data = {}
        data[ 'count' ] = int(output[0].split(':')[1].strip())
        data[ 'machines' ] = [vmx.strip() for vmx in output[1:]] 

        return data

    def start( self, vmx, gui=True ):
        vmx = get_abspath( vmx )

        file_must_exist( 'VMX', vmx )

        gui_value = ( 'nogui', 'gui' )[gui]
        self.__vmrun( [ 'start', vmx, gui_value ] )
    
    def stop( self, vmx, soft=True ):
        vmx = get_abspath( vmx )

        file_must_exist( 'VMX', vmx )

        soft_value = ( 'hard', 'soft' )[soft]
        self.__vmrun( [ 'stop', vmx, soft_value ] )
    
    def reset( self, vmx, soft=True ):
        vmx = get_abspath( vmx )

        file_must_exist( 'VMX', vmx )
        
        soft_value = ( 'hard', 'soft' )[soft]
        self.__vmrun( [ 'reset', vmx, soft_value ] )
    
    def suspend( self, vmx, soft=True ):
        vmx = get_abspath( vmx )

        file_must_exist( 'VMX', vmx )
        
        soft_value = ( 'hard', 'soft' )[soft]
        self.__vmrun( [ 'suspend', vmx, soft_value ] )
    
    def pause( self, vmx ):
        vmx = get_abspath( vmx )

        file_must_exist( 'VMX', vmx )

        self.__vmrun( [ 'pause', vmx ] )
    
    def unpause( self, vmx ):
        vmx = get_abspath( vmx )

        file_must_exist( 'VMX', vmx )

        self.__vmrun( [ 'unpause', vmx ] )

    def delete( self, vmx ):
        vmx = get_abspath( vmx )

        file_must_exist( 'VMX', vmx )
        
        self.__vmrun( [ 'delete', vmx ] )

class vdiskmanager_cli( object ):
    # Valid disks
    SPARSE_SINGLE = 'SPARSE_SINGLE'
    SPARSE_SPLIT = 'SPARSE_SPLIT'
    PREALLOC_SINGLE = 'PREALLOC_SINGLE'
    PREALLOC_SPLIT = 'PREALLOC_SPLIT'
    disk_type_map = {
        'SPARSE_SINGLE': '0',
        'SPARSE_SPLIT': '1',
        'PREALLOC_SINGLE': '2',
        'PREALLOC_SPLIT': '3'
    }

    # Valid adapters
    IDE = 'ide'
    LSILOGIC = 'lsilogic'
    BUSLOGIC = 'buslogic'
    adapters = [ IDE, LSILOGIC, BUSLOGIC ]

    """Human readable python interface to the vmware-vdiskmanager cli of VMware Fusion.

    Tested with VMware Fusion 5."""

    def __init__( self, bundle_directory=None ):
        if not bundle_directory:
            bundle_directory = '/Applications/VMware Fusion.app'

        vmrun = os.path.join( bundle_directory, 'Contents/Library/vmware-vdiskmanager' )

        if not os.path.isfile( vmrun ):
            raise ValueError( "vmrun tool not found at path {0}".format( vmrun ) )

        self.tool_path = vmrun

    def __vdiskmanager( self, command ):
        base = [ self.tool_path ]
        base.extend( command )
        
        proc = subprocess.call( base )

    def create( self, vmdk, size, disk_type=None, adapter_type=None ):
        file_must_not_exist( 'VMDK', vmdk )

        # disk type
        if not disk_type:
            disk_type = self.SPARSE_SPLIT

        if disk_type not in self.disk_type_map:
            raise ValueError( "Invalid disk type {0}".format( disk_type ) )

        # adapter type
        if not adapter_type:
            adapter_type = self.LSILOGIC

        if adapter_type not in self.adapters:
            raise ValueError( "Invalid adapter type {0}".format( adapter_type ) )

        self.__vdiskmanager( [ '-c', '-s', size, '-a', adapter_type, '-t', self.disk_type_map[ disk_type ], vmdk ] )

    def defragment( self, vmdk ):
        file_must_exist( 'VMDK', vmdk )

        self.__vdiskmanager( [ '-d', vmdk ] )

    def shrink( self, vmdk ):
        file_must_exist( 'VMDK', vmdk )

        self.__vdiskmanager( [ '-k', vmdk ] )

    def rename( self, source_vmdk, destination_vmdk ):
        file_must_exist( 'VMDK', source_vmdk )
        file_must_not_exist( 'VMDK', destination_vmdk )

        self.__vdiskmanager( [ '-n', source_vmdk, destination_vmdk ] )

    def convert( self, vmdk, disk_type ):
        file_must_exist( 'VMDK', vmdk )

        if disk_type not in self.disk_type_map:
            raise ValueError( "Invalid disk type {0}".format( disk_type ) )

        self.__vdiskmanager( [ '-r', '-t', self.disk_type_map[ disk_type ], vmdk ] )

    def expand( self, vmdk, new_size ):
        file_must_exist( 'VMDK', vmdk )

        self.__vdiskmanager( [ '-x', size, vmdk ] )

class dhcpd_leases( object ):
    """A dhcpd_leases contains a mapping between MAC and IP addresses from the
    content of a given dhpcd.leases file.

    When the lease file contains multiple leases for the same mac address, the
    lease with the latest start date is used."""

    def __init__( self, lease_file ):
        if not os.path.isfile( lease_file ):
            raise ValueError( "dhcpd.leases '{0}' not found".format( lease_file ) )

        self.lease_file = lease_file
        self.list = {}

    def __parse( self ):
        LBRACE, RBRACE, SEMI, QUOTE = map(Suppress,'{};"')
        ipAddress = Combine(Word(nums) + ('.' + Word(nums))*3)
        hexint = Word(hexnums,exact=2)
        macAddress = Combine(hexint + (':'+hexint)*5)
        hdwType = Word(alphanums)
        yyyymmdd = Combine((Word(nums,exact=4)|Word(nums,exact=2))+('/'+Word(nums,exact=2))*2)
        hhmmss = Combine(Word(nums,exact=2)+(':'+Word(nums,exact=2))*2)
        dateRef = oneOf(list("0123456"))("weekday") + yyyymmdd("date") + hhmmss("time")
        def to_datetime(tokens):
            tokens["datetime"] = datetime.strptime("%(date)s %(time)s" % tokens, "%Y/%m/%d %H:%M:%S")
        dateRef.setParseAction(to_datetime)
        startsStmt = "starts" + dateRef + SEMI
        endsStmt = "ends" + (dateRef | "never") + SEMI
        tstpStmt = "tstp" + dateRef + SEMI
        tsfpStmt = "tsfp" + dateRef + SEMI
        hdwStmt = "hardware" + hdwType("type") + macAddress("mac") + SEMI
        uidStmt = "uid" + QuotedString('"')("uid") + SEMI
        bindingStmt = "binding" + Word(alphanums) + Word(alphanums) + SEMI
        leaseStatement = startsStmt | endsStmt | tstpStmt | tsfpStmt | hdwStmt |  uidStmt | bindingStmt
        leaseDef = "lease" + ipAddress("ipaddress") + LBRACE +  Dict(ZeroOrMore(Group(leaseStatement))) + RBRACE

        with open(  self.lease_file, 'r' ) as file:

            parsed = leaseDef.scanString( file.read() )

            return parsed

    def load( self ):
        all_leases = {}

        for lease, start, stop in self.__parse():
            try:
                mac = lease.hardware.mac

                if mac not in all_leases or lease.starts.datetime > all_leases[mac].starts.datetime:
                    all_leases[ mac ] = lease

            except AttributeError, e:
                print e

        for mac in all_leases:
            all_leases[ mac ] = all_leases[ mac ].ipaddress

        self.list = all_leases

    reload = load

    def __len__( self ):
        return len( self.list )

    def __iter__( self ):
        return self.list.iterkeys()

    def __getitem__( self, item ):
        return self.list[ item ]

    def __contains__( self, item ):
        return item in self.list

    def __str__( self ):
        return str( self.list )

    def __repr__( self ):
        return repr( self.list )

class vnet_cli(object):
    def __init__( self, name ):
        self.name = name
        self.leases = dhcpd_leases( '/var/db/vmware/vmnet-dhcpd-' + name + '.leases' )
        self.leases.load()

# Default access
vmrun = vmrun_cli()
vdiskmanager = vdiskmanager_cli()
vmnet_hostonly = vnet_cli( 'vmnet1' )
vmnet_nat = vnet_cli( 'vmnet8' )
