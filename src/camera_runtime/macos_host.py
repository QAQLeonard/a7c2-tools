"""Release only this Sony camera's mounted media before libusb capture.

Follows MDHan/a7c2-fl23-macos at 1491f734df07f02fb77da6ea7062828bce0e30e7:
stable camera disks, non-forced unmountDisk and a re-check, all before the
first libusb open; after a service stop, wait for the user's MSC choice.
No forced unmount, driver installation, service authentication or firmware I/O.
"""
import plistlib
import re
import subprocess
import sys
import time

STABLE_SECONDS=3
STABLE_TIMEOUT=20
NORMAL_RETURN_SECONDS=60
MSC_PROMPT='If the camera screen asks for the USB connection mode, choose item 2, "Image Transfer (MSC)".'


def registry_nodes(tree):
    if isinstance(tree,list):
        for item in tree:yield from registry_nodes(item)
    elif isinstance(tree,dict):
        yield tree
        yield from registry_nodes(tree.get('IORegistryEntryChildren',[]))


# Characters XML 1.0 forbids. Some devices publish names containing them, and
# a single such property made the whole registry unparsable (field log 38).
INVALID_XML=re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def plist_command(*command,lenient=False):
    result=subprocess.run(command,capture_output=True,timeout=30)
    if result.returncode:
        print(result.stdout.decode('utf-8',errors='replace'),flush=True)
        print(result.stderr.decode('utf-8',errors='replace'),file=sys.stderr,flush=True)
        raise RuntimeError('macOS command failed (%s): %s'%(result.returncode,' '.join(command)))
    data=result.stdout
    if lenient:
        # Only other devices' free-text names are affected; IDs and BSD names are plain ASCII.
        data=INVALID_XML.sub('',data.decode('utf-8',errors='replace')).encode('utf-8')
    return plistlib.loads(data)


def camera_media():
    """Registry identity and verified disks of the one connected camera."""
    # USB device subtrees only, not the whole registry. A camera behind a hub
    # appears under the hub's subtree and as its own root, so de-duplicate.
    tree=plist_command('/usr/sbin/ioreg','-p','IOService','-r','-c','IOUSBHostDevice','-l','-a',lenient=True)
    found={}
    for node in registry_nodes(tree):
        if (node.get('idVendor')==0x054c and node.get('idProduct')==0x0e8a
                and node.get('IOObjectClass')=='IOUSBHostDevice'):
            found.setdefault(node.get('IORegistryEntryID',id(node)),node)
    cameras=list(found.values())
    if len(cameras)!=1:raise RuntimeError('Connect exactly one A7C II in Mass Storage mode, then prepare the USB connection. '+MSC_PROMPT)
    registry=cameras[0].get('IORegistryEntryID')
    if registry is None:raise RuntimeError('Missing camera USB registry identity')
    # Disk identifiers come only from the selected USB device's registry
    # subtree, never from all external disks or every mounted /Volumes path.
    media={}
    for node in registry_nodes(cameras[0]):
        if node.get('IOObjectClass')!='IOMedia' or not node.get('BSD Name'):continue
        disk=node['BSD Name']
        if not re.fullmatch(r'disk[0-9]+(?:s[0-9]+)*',disk):
            raise RuntimeError('Unexpected camera disk identifier: '+disk)
        info=plist_command('/usr/sbin/diskutil','info','-plist','/dev/'+disk)
        if (info.get('DeviceIdentifier')!=disk or info.get('Internal') is not False
                or info.get('BusProtocol')!='USB'):
            raise RuntimeError('Camera disk external-USB identity check failed: '+disk)
        whole=info.get('WholeDisk') is True
        # diskutil reports ParentWholeDisk for partitions, not the whole disk.
        media[disk]=dict(parent=disk if whole else info.get('ParentWholeDisk'),whole=whole,
                         mount=info.get('MountPoint') or None)
    for row in media.values():
        if row['parent'] not in media or not media[row['parent']]['whole']:
            raise RuntimeError('Camera disk parent is not a verified camera disk')
    return registry,media


def wait_for_stable_media():
    # A just-connected camera may still be publishing or mounting disks.
    deadline=time.monotonic()+STABLE_TIMEOUT
    previous=stable_since=None
    while True:
        registry,media=camera_media()
        topology=(registry,tuple(sorted((disk,row['parent'],row['whole']) for disk,row in media.items())))
        now=time.monotonic()
        # MSC service access also works without an SD card. A stable empty
        # subtree has nothing to unmount; it must not become a readiness gate.
        if topology!=previous:previous,stable_since=topology,now
        elif now-stable_since>=STABLE_SECONDS:return
        if now>=deadline:
            raise RuntimeError('The camera disk is not stable yet; USB has not been taken over. '+MSC_PROMPT+' Wait for the access light to stop, then retry.')
        time.sleep(.5)


def unmount_camera():
    wait_for_stable_media()
    registry,media=camera_media()
    unmounted=[]
    for disk in sorted(name for name,row in media.items() if row['whole']):
        now,current=camera_media()
        if now!=registry or set(current)!=set(media):
            raise RuntimeError('The camera or disk changed before unmounting; USB has not been taken over. Reconnect and retry.')
        print('Unmounting the camera disk (do not unplug): '+disk,flush=True)
        result=subprocess.run(['/usr/sbin/diskutil','unmountDisk','/dev/'+disk],
                              capture_output=True,text=True,timeout=30)
        print(result.stdout,flush=True)
        if result.stderr:print(result.stderr,file=sys.stderr,flush=True)
        if result.returncode:
            raise RuntimeError('Cannot unmount the camera volume. Close Photos, Image Capture and any app using the memory card, then retry.')
        unmounted.append(disk)
    now,current=camera_media()
    if now!=registry or set(current)!=set(media) or any(row['mount'] for row in current.values()):
        raise RuntimeError('Not all camera volumes could be unmounted; USB has not been taken over. Close Photos, Image Capture and any app using the memory card, then retry.')
    return dict(unmounted=unmounted,camera_firmware_written=False)


def claim_camera_interface(device,interface_class=None):
    """libusb ownership after storage has unmounted; no authentication retry."""
    import usb.util
    detached=False
    try:
        if interface_class is not None:
            interface=device.get_active_configuration()[(0,0)]
            found=(interface.bInterfaceClass,interface.bInterfaceSubClass,interface.bInterfaceProtocol)
            if found!=interface_class:raise RuntimeError('Unexpected camera USB interface: %r'%(found,))
        if device.is_kernel_driver_active(0):
            device.detach_kernel_driver(0);detached=True
        usb.util.claim_interface(device,0)
    except BaseException:
        try:
            if detached:device.attach_kernel_driver(0)
        finally:usb.util.dispose_resources(device)
        raise


def wait_normal_return(find):
    """After a service stop, wait for the camera's normal MSC identity.

    A timeout is reported, not raised: the finished camera work is known and
    the next connection checks the identity again.
    """
    import usb.core
    print('Service mode exited; waiting for the normal USB connection (up to %d seconds). '%NORMAL_RETURN_SECONDS+MSC_PROMPT,flush=True)
    deadline=time.monotonic()+NORMAL_RETURN_SECONDS
    last_error=None
    while True:
        try:device=find()
        except (RuntimeError,usb.core.USBError) as exc:
            detail=str(exc)
            if detail!=last_error:print('Waiting for normal USB to re-enumerate: '+detail,flush=True)
            last_error=detail;device=None
        if device is not None:
            import usb.util
            usb.util.dispose_resources(device)
            print('Normal USB connection restored.',flush=True)
            return True
        if time.monotonic()>=deadline:
            print('Normal USB connection not restored within %d seconds. Before the next operation, choose "Image Transfer (MSC)" on the camera.'%NORMAL_RETURN_SECONDS,flush=True)
            return False
        time.sleep(.5)
