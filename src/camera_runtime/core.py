"""Portable, offline validation and per-body planning. No USB imports here."""
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys

BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'vendor'))
MODEL='ILCE-7CM2'
VERSION='2.01'
ORIGINAL=['2ea02f7ecbc5bb917316fe8ef4ce5ffd87eb66efaae78ba2ce11420552df539b',
          'f5a477588698ef965748903b8959a39ce4f59ffd4aee4d4234ef1670f56a1428']
FINAL=['1aaeb8fbe0297950cab454d498d1a5ba874f91542aa2737aae27a73971e324d7',
       '442c9261d7c76c30f65e5b66ae133fea40fc31ee6c0046ff78b6b45df8ab455c']
PROGRAMS=['appFw.so','cpapp-b.bin']
CP_KEYS=[0x02a40001,0x02a4000d]
AP_KEYS=[0x02cf1287,0x02cf1289]
COLOUR_SLOTS=[(55,23),(56,25)]
NATIVE_PATHS={'libJit.so','a7c2.install.request','a7c2.install.result','a7c2.probe.result',
              'a7c2.wbi.request','a7c2.wbi.result','a7c2.runtime.result','a7c2-preview-staged.so'}

def sha(data):return hashlib.sha256(data).hexdigest()
def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2);f.flush()
        __import__('os').fsync(f.fileno())
    temp.replace(path)

def assets():
    manifest=read_json(BASE/'assets/manifest.json')
    names={'installer.so','probe.so','wbi.so','runtime.so','patches.json','colors.json'}
    if not names.issubset(manifest['files']):raise ValueError('Package asset manifest mismatch')
    for name in manifest['files']:
        if not (BASE/'assets'/name).is_file():raise ValueError('Package is missing a file: '+name)
    return manifest

def backup_records(raw):
    from pmca.backup import BackupFile
    result=[]
    for m in re.finditer(b'BK4\0',raw):
        try:b=BackupFile(io.BytesIO(raw[m.start()-12:]))
        except Exception:continue
        result.append(dict(b.listProperties()))
    if len(result)!=2:raise ValueError('Body backup must contain two BK4 files with valid checksums')
    return result

def patch_program(original,chip,reverse=False):
    data=read_json(BASE/'assets/patches.json')[chip]
    # No firmware-provenance whitelist: guard only bytes we actually replace.
    spans=[]
    for w in data['writes']:
        offset=int(w['file_offset'],16)
        before=bytes.fromhex(w['after_hex'] if reverse else w['before_hex'])
        after=bytes.fromhex(w['before_hex'] if reverse else w['after_hex'])
        if (not before or len(before)!=len(after) or offset<0 or offset+len(before)>len(original)
            or original[offset:offset+len(before)]!=before):raise ValueError('Patch window precondition mismatch')
        spans.append((offset,before,after))
    spans.sort()
    if any(a[0]+len(a[1])>b[0] for a,b in zip(spans,spans[1:])):raise ValueError('Patch windows overlap')
    result=bytearray(original)
    for offset,before,after in spans:result[offset:offset+len(before)]=after
    if len(result)!=len(original):raise ValueError('Candidate file length was changed')
    return bytes(result)


def merge_colors(unit01,unit0d):
    if len(unit01)!=8192 or len(unit0d)!=28672:raise ValueError('Colour unit length mismatch')
    a,b=bytearray(unit01),bytearray(unit0d)
    for row in read_json(BASE/'assets/colors.json'):
        parameter,slot=row['parameter'],row['slot']
        if (parameter,slot) not in COLOUR_SLOTS:raise ValueError('Colour mapping mismatch')
        if unit01[0x1200+parameter] or unit0d[0x196+parameter]:raise ValueError('Target parameter already in use; refusing to overwrite')
        if slot in unit01[0x1200:0x1250] or slot in unit0d[0x196:0x196+74]:raise ValueError('Target colour slot is already referenced by another parameter')
        c=0x1250+slot*64;m=0x1e0+slot*768
        if any(unit01[c:c+64]) or any(unit0d[m:m+576]):raise ValueError('Target colour slot already contains data')
        chroma,matrix=colour_record(row)
        a[0x1200+parameter]=slot;b[0x196+parameter]=slot
        a[c:c+64]=chroma;b[m:m+576]=matrix
    # Check every existing look's mapping and complete referenced records.
    for p in range(55):
        c=unit01[0x1200+p];m=unit0d[0x196+p]
        if a[0x1200+p]!=c or b[0x196+p]!=m:raise ValueError('Existing style mapping was changed')
        if a[0x1250+c*64:0x1250+c*64+64]!=unit01[0x1250+c*64:0x1250+c*64+64]:raise ValueError('Existing colour record was changed')
        if m<32 and b[0x1e0+m*768:0x1e0+m*768+576]!=unit0d[0x1e0+m*768:0x1e0+m*768+576]:raise ValueError('Existing matrix was changed')
    return bytes(a),bytes(b)

def runtime_counter(chip,key,a,b):
    if chip or a.attr!=b.attr:return False
    if key==0x01070000 and len(a.data)==len(b.data)==8:
        return 0<=int.from_bytes(b.data,'little')-int.from_bytes(a.data,'little')<=1000000
    if key==0x02780000 and len(a.data)==len(b.data)==256:
        delta=int.from_bytes(b.data[24:28],'little')-int.from_bytes(a.data[24:28],'little')
        return a.data[:24]==b.data[:24] and a.data[28:]==b.data[28:] and 0<delta<=1000000
    return False

def verify_preservation(before,after,expected):
    kept=0;telemetry=[]
    for chip in [0,1]:
        if set(before[chip])!=set(after[chip]):raise ValueError('Set of setting entries changed')
        for key,a in before[chip].items():
            b=after[chip][key]
            if (chip,key) in expected:
                if b.data!=expected[chip,key] or b.attr!=a.attr:raise ValueError('Target setting readback mismatch')
            elif (a.data,a.attr)==(b.data,b.attr):kept+=1
            elif runtime_counter(chip,key,a,b):telemetry.append(hex(key))
            else:raise ValueError(f'Unexpected extra setting change: chip{chip}/{key:#x}; save the records and review')
    return {'preserved_properties':kept,'runtime_counters':telemetry}

def parse_native(name,raw,mode=None):
    if name=='installer':
        if len(raw)!=240:raise ValueError('Installer result length mismatch')
        v=struct.unpack_from('<8sIIIIqqqqqqqQQQQ',raw)
        if v[:3]!=(b'A7IRP001',1,mode) or v[3]!=9 or any(v[i] for i in [5,6,7,8,9,10]):
            raise ValueError('Installer did not fully succeed; do not retry or restart')
        before=[raw[112:144].hex(),raw[144:176].hex()]
        after=[raw[176:208].hex(),raw[208:240].hex()]
        if before!=(FINAL if mode==2 else ORIGINAL):raise ValueError('Full-file hash mismatch before write')
        if mode and after!=(ORIGINAL if mode==2 else FINAL):raise ValueError('Full-file hash mismatch after write')
        if mode==0 and v[4]!=0:raise ValueError('Verify-only mode reported non-zero writes')
        return {'mode':mode,'window_writes':v[4],'before':before,'after':after,'readonly_verified':True}
    if name=='probe':
        if len(raw)<72:raise ValueError('Diagnostic result too short')
        v=struct.unpack_from('<8sIIqqqqQIIII',raw)
        if v[:3]!=(b'A7PRB001',1,16) or any(v[i] for i in [3,4,6]) or len(raw)!=72+sum(v[8:11]):
            raise ValueError('Model field, permissions or diagnostic result mismatch')
        mounts=raw[72+v[8]:72+v[8]+v[9]]
        usr=[line.split() for line in mounts.splitlines() if len(line.split())>=4 and line.split()[1]==b'/usr']
        readonly=(b'ro' in usr[0][3].split(b',')) if len(usr)==1 and usr[0][0]==b'/dev/nflasha15' and usr[0][2]==b'ext2' else None
        return {'model_index':v[2],'product_column':9,'root_verified':True,'usr_mount_readonly':readonly}
    if name=='wbi':
        if len(raw)!=192:raise ValueError('Boot snapshot result length mismatch')
        v=struct.unpack('<8sII9q16s16s32s32sII',raw)
        if v[:3]!=(b'A7WBR001',1,mode) or any(v[i] for i in [3,4,5]):raise ValueError('Boot snapshot handling not verified; do not run it again')
        if v[12].rstrip(b'\0')!=b'2\n' or v[14].rstrip(b'\0')!=b'*wbi4\n':raise ValueError('Unsupported boot snapshot starting state')
        if mode and (v[7]!=1 or v[9]!=1 or any(v[i] for i in [8,10,11]) or not v[16]
                     or v[13].rstrip(b'\0')!=b'0\n' or v[15].rstrip(b'\0')!=b'*wbi4\n'):
            raise ValueError('Boot snapshot write or readback incomplete')
        return {'mode':mode,'verified':True,'fresh_drop_log':bool(v[16])}
    if name=='runtime':
        if len(raw)!=1832:raise ValueError('Runtime result length mismatch')
        v=struct.unpack_from('<8sIIqqqQII',raw)
        if v[:3]!=(b'A7RUN001',1,6) or v[3] or v[4] or v[7]!=16:raise ValueError('Runtime identity/result mismatch')
        spans=[]
        for i,(offset,n) in enumerate([(0x3528804,112),(0x4b2ed19,2),(0x59892b8,40),(0x5989370,40),(0x4b4a5e4,12),(0x4b3b544,12)]):
            spans.append({'offset':offset,'length':n,'memory':raw[56+i*256:56+i*256+n].hex(),
                          'disk':raw[56+i*256+128:56+i*256+128+n].hex()})
        return {'spans':spans,'image_mode':raw[1592:1608].split(b'\0')[0].decode('ascii','replace'),
                'boot_id':raw[1768:1832].split(b'\0')[0].decode('ascii','replace')}
    raise ValueError('Unknown native module')

def slot_row_sums(block):
    """Three row sums of a 12-byte slot's six coefficients expanded to 3x3 (all should be 1024 so neutral input stays neutral)."""
    a,b,c,d,e,f=struct.unpack('<6h',block)
    return (a+b+1024-a-b, -c+c+d+1024-d, -e-f+e+f+1024)

def colour_record(row):
    """Check a colour record: lengths, last eight chroma entries zero, expanded row sums of all 48 slots, equal to the donor target.

    A 576-byte matrix record = three 192-byte endpoints B/A1/A2, each with 16 slots x 12 bytes (six coefficients).
    Before 0.4.x the 16 slots of each endpoint were filled with one set of coefficients; in native looks on the
    camera the 16 slots differ (15-16 distinct values within one bank and endpoint), and 0x780F also packs them
    slot by slot, so 0.5.0 copies the donor values per slot (see git history,
    commit 05f3cd2, src/fl23/docs/fl23-v050-gamma-and-perslot-matrix.md).

    Endpoints no longer have to be internally uniform. Instead every slot's expanded row sums must be 1024
    (structural check), and the whole record must equal the target in assets/fx2_fl23_donor.json byte for byte
    (content check). The latter keeps this tool's strict stance: no "some slots new, some old" mix and no value
    without donor evidence may enter the install flow.
    """
    chroma=bytes.fromhex(row['chroma']);matrix=bytes.fromhex(row['matrix'])
    if len(chroma)!=64 or len(matrix)!=576:raise ValueError('Colour record length mismatch')
    if any(chroma[48:]):raise ValueError('Colour record: last eight chroma entries are non-zero')
    for index in range(0,576,12):
        if any(s!=1024 for s in slot_row_sums(matrix[index:index+12])):
            raise ValueError(f'Slot {index//12} expanded row sums are not 1024; refusing to write')
    for look in read_json(BASE/'assets/fx2_fl23_donor.json')['looks']:
        if look['target_parameter']!=row['parameter'] or look['target_slot']!=row['slot']:
            continue
        want_chroma=b''.join(struct.pack('<8h',*group) for group in look['cc1_int16'])+bytes(16)
        want_matrix=b''.join(struct.pack('<6h',*ab)
                             for name in ('B','A1','A2') for ab in look['matrix_slots'][name])
        if chroma!=want_chroma:raise ValueError('Chroma does not equal the donor target')
        if matrix!=want_matrix:raise ValueError('Matrix does not equal the donor target (per slot)')
        return chroma,matrix
    raise ValueError('Unknown colour parameter/slot combination; refusing to write')

def colour_write_spans():
    """Byte ranges merge_colors overwrites, grouped by CP unit index (half-open intervals).

    Index 0 is unit-02a40001 (8192 bytes), 1 is unit-02a4000d (28672 bytes).
    This lets the restore flow tell "colours written by some version of this tool" from "content of unknown origin":
    as long as everything outside the windows matches the original, the windows can safely be rewritten to the
    original whichever version wrote them.
    """
    spans={0:[],1:[]}
    for parameter,slot in COLOUR_SLOTS:
        spans[0].append((0x1200+parameter,0x1201+parameter))
        spans[0].append((0x1250+slot*64,0x1250+slot*64+64))
        spans[1].append((0x196+parameter,0x197+parameter))
        spans[1].append((0x1e0+slot*768,0x1e0+slot*768+576))
    merged={}
    for index,regions in spans.items():
        out=[]
        for start,end in sorted(regions):
            if out and start<=out[-1][1]:out[-1]=(out[-1][0],max(out[-1][1],end))
            else:out.append((start,end))
        merged[index]=out
    return merged

def matches_outside_colour(current,original,index):
    """Whether current matches original exactly outside the colour write windows."""
    if len(current)!=len(original):return False
    cursor=0
    for start,end in colour_write_spans()[index]:
        if current[cursor:start]!=original[cursor:start]:return False
        cursor=max(cursor,end)
    return current[cursor:]==original[cursor:]

def colour_window_diff(current,original,index):
    """Offset of the first difference outside the colour write windows; None if there is none."""
    if len(current)!=len(original):return 'len'
    skip=[]
    for start,end in colour_write_spans()[index]:skip.append((start,end))
    for offset in range(len(current)):
        if current[offset]==original[offset]:continue
        if any(start<=offset<end for start,end in skip):continue
        return offset
    return None
