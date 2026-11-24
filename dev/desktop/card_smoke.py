"""Focused frozen application contract check; no device access or firmware build."""
from pathlib import Path
import tempfile,zlib

def run():
    from desktopapp import VERSION,firmwarelocal,firmwarefactory,sshupdates,startup,sshboot
    assert VERSION=='3.11'and sshupdates.prepare_version_restore.__kwdefaults__['source_version']==VERSION
    assert 'update_header_version=OFFICIAL_VERSION'in Path(firmwarefactory.__file__).read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='c2-card-contract-')as temp:
        path=Path(temp)/'target';path.write_bytes(b'BBBB')
        target={'0700_part_image/dev/nflasha8':path}
        row=b'0,00000000,00000004,000001a4,0,0,root,root,-1,-1,dev/nflasha8,\n'
        failures=[]
        for label,raw in [('missing',b''),('duplicate',row+row)]:
            try:firmwarelocal.rewrite_sum(raw,target)
            except ValueError:failures.append(label)
        assert failures==['missing','duplicate']
        actual,matched=firmwarelocal.rewrite_sum(row,target)
        assert matched==list(target)and actual.split(b',')[1]==f'{zlib.crc32(b"BBBB"):08x}'.encode()
        try:firmwarelocal.default_template_names([])
        except ValueError:pass
        else:raise AssertionError('Missing default templates accepted')
    sample=b'#!/bin/sh\nif true; then\n    /usr/bin/bootin.elf &\nfi\n'
    revised=sshboot.patch_startup(sample)
    assert revised.index(b'sh /log/a7c2-start.sh || :')<revised.index(b'bootin.elf &')<revised.index(b'wifi-ssh')
    return dict(version=VERSION,missing_CRC_rejected=True,duplicate_CRC_rejected=True,
                missing_templates_rejected=True,normal_CRC_updated=True,recovery_version=firmwarefactory.OFFICIAL_VERSION,
                default_source_version=VERSION,device_io=False,log_script_hook=True,SD_initialization_verified=False,WBI_changed=False,
                full_card_flash_verified=False)
