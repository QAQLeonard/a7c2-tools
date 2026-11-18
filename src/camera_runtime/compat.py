"""Version-scoped FL23 planning without a firmware-provenance whitelist.

Only edited bytes have conflict guards; full readback compares bytes.
"""
from pathlib import Path
import sys
import core

WARNING='Firmware origin is not verified. Firmware modified outside this repository may conflict with FL23 and stop the camera from starting normally; keep your backups.'
LEGACY_CONVERTER=bytes.fromhex('e1000035002800511f1400718800005400e4031140000039c0035fd63f2c007188020054800000100048613840000039c0035fd600030201100f1112050d13141f2003d51f2003d51f2003d51f2003d51f2003d51f2003d51f2003d51f2003d51f2003d51f2003d51f2003d51f2003d5')


def modules():
    sys.path.insert(0,str(core.BASE.parent/'looks'))
    try:
        from looktool import device_layout,firmware,nativebuild,worker
    except ImportError as exc:
        raise ValueError('LUT compatibility mode is missing dependencies; update the complete tool and reopen FL23.cmd.') from exc
    return device_layout,firmware,nativebuild,worker


def plan(ap,cp,version=core.VERSION,*,transitions=True):
    if version!=core.VERSION:raise ValueError('FL23 supports ILCE-7CM2 firmware 2.01 only; enter the version shown on the camera version page')
    layout,firmware,_,_=modules()
    before=dict(zip(core.PROGRAMS,[ap,cp]))
    # These are instruction-boundary checks, not file-source fingerprints.
    # A LUT converter already handles native FL2/FL3 and must not be replaced.
    template=ap[0x35287f0:0x3528874].hex();templates=layout.runtime()['ap_templates']
    lut=template in templates or ap[0x3528804:0x3528874]==LEGACY_CONVERTER
    mask=templates.index(template) if template in templates else None
    manifest=core.read_json(core.BASE/'assets/patches.json')
    if lut:
        for at,expected in [(0x138814,bytes.fromhex('3720e7e7')),(0x13882e,bytes.fromhex('3820dae7'))]:
            if cp[at:at+len(expected)]!=expected:raise ValueError(f'CP FL23 call site conflict: {at:#x}; nothing written')
    after={};regions={};changed=False
    for chip,name in enumerate(core.PROGRAMS):
        source=before[name];result=bytearray(source);spans=[]
        for w in manifest[chip]['writes']:
            at=int(w['file_offset'],16);old,new=bytes.fromhex(w['before_hex']),bytes.fromhex(w['after_hex'])
            if lut and at==0x3528804:continue
            if lut and chip==1:
                native=next((entry for entry in layout.fl23_native_windows() if entry[0]==at),None)
                if native is None:continue
                current=source[at:at+len(new)]
                if current==new:continue
                if current not in (old,native[3],*layout.fl23_previous_values(at)):raise ValueError(f'CP FL23 native curve/mode site conflict: {at:#x}')
                result[at:at+len(new)]=new;changed=True
                for offset in range(0,len(new),4096):spans.append((at+offset,min(4096,len(new)-offset)))
                continue
            if len(old)!=len(new) or at+len(old)>len(source):raise ValueError(f'Patch site out of range: {name} {at:#x}')
            current=source[at:at+len(old)]
            if current==new:continue
            if current!=old and not (chip==1 and current in layout.fl23_previous_values(at)):
                detail=current[:64].hex()
                raise ValueError(f'Patch site conflict: {name} {at:#x}; nothing written; '
                    f'current bytes ({len(current)} bytes, first 64)={detail}. '
                    'If an older version was used, follow the README to factory restore first, then install; keep this log.')
            result[at:at+len(new)]=new;changed=True
            for offset in range(0,len(new),4096):spans.append((at+offset,min(4096,len(new)-offset)))
        if chip==1:
            from looktool import photoio,photobuild
            if photoio.present(source):
                refreshed=photoio.refresh_gamma_table(bytes(result))
                if refreshed!=result:
                    result=bytearray(refreshed);changed=True
                    spans.append((photobuild.TABLE_FILE,50*28))
        after[name]=bytes(result);regions[name]=spans
    identity={'kind':'lut' if lut else 'version-2.01','mask':mask,'provenance_checked':False,'firmware_version':version,'version_source':'user-camera-version-screen'}
    if not changed:return identity,True,before,None,None
    if not transitions:return identity,False,after,None,None
    forward=firmware.transition(before,after,regions)
    reverse=firmware.transition(after,before,regions)
    if firmware.apply(firmware.apply(before,forward),reverse)!=before:
        raise ValueError('Full restore candidate mismatch')
    return identity,False,after,forward,reverse


def prepare(root,ap,cp,version=core.VERSION):
    identity,enabled,after,_,_=plan(ap,cp,version,transitions=False)
    result={'identity':identity,'already_enabled':enabled}
    if not enabled:
        from looktool.checkpointworker import build_programs
        result['byte_builds']=build_programs(dict(zip(core.PROGRAMS,[ap,cp])),after,root/'compat-worker',checkpoint_namespace=False)
    for n,data in after.items():(root/'candidate'/n).write_bytes(data)
    return result


def validate(root,state):
    spec=state['compatibility']
    ap,cp=[(root/'original'/(n+'.bin')).read_bytes() for n in core.PROGRAMS]
    identity,enabled,after,_,_=plan(ap,cp,state.get('version',core.VERSION),transitions=False)
    if spec['identity']!=identity or spec['already_enabled']!=enabled:
        raise ValueError('Compatibility job source or target has changed')
    for n,data in after.items():
        if (root/'candidate'/n).read_bytes()!=data:raise ValueError('Compatibility candidate has changed')


def validate_enabled_colors(a,b):
    # Undo only the exact FL23 colour records, then re-merge. This proves
    # ownership without clearing calibration, user recipes or LUT tables.
    x,y=bytearray(a),bytearray(b)
    if len(x)!=8192 or len(y)!=28672:raise ValueError('Colour unit length mismatch')
    for row in core.read_json(core.BASE/'assets/colors.json'):
        p,s=row['parameter'],row['slot'];x[0x1200+p]=0;y[0x196+p]=0
        x[0x1250+s*64:0x1250+(s+1)*64]=bytes(64)
        y[0x1e0+s*768:0x1e0+s*768+576]=bytes(576)
    if core.merge_colors(bytes(x),bytes(y))!=(a,b):raise ValueError('Existing FL23 colour data is incomplete; refusing to rewrite')
