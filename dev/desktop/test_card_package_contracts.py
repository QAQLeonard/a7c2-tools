"""New failure cases found during card-update review; no camera/VM access."""
import ast,copy,io,json,struct,tarfile,zlib
from pathlib import Path
import pytest
from desktopapp import VERSION,firmwarelocal,firmwarefactory,sshupdates


def test_crc_missing_and_duplicate_targets_reject(tmp_path):
    target=tmp_path/'image';target.write_bytes(b'BBBB')
    mapping={'0700_part_image/dev/nflasha8':target}
    with pytest.raises(ValueError,match='missing'):
        firmwarelocal.rewrite_sum(b'0,00000000,00000004,000001a4,0,0,root,root,-1,-1,dev/nflasha7,\n',mapping)
    line=b'0,00000000,00000004,000001a4,0,0,root,root,-1,-1,dev/nflasha8,\n'
    with pytest.raises(ValueError,match='Duplicate'):firmwarelocal.rewrite_sum(line+line,mapping)
    changed,ledger=firmwarelocal.rewrite_sum(line,mapping)
    assert ledger==list(mapping)and changed.split(b',')[1]==f'{zlib.crc32(b"BBBB"):08x}'.encode()
    assert firmwarelocal.rewrite_sum(line,{})==(line,[])


def test_complete_template_set_is_required():
    names=['CX89700_ALLLANG']+['region'+str(i)for i in range(11)]
    members=[tarfile.TarInfo('0110_backup/SYSIPSX-DSLR/PP/'+n+'.bin')for n in names]
    assert len(firmwarelocal.default_template_names(members))==12
    for bad in (members[:-1],members+[members[-1]],members[:-1]+[members[0]]):
        with pytest.raises(ValueError):firmwarelocal.default_template_names(bad)


def test_version_defaults_follow_311():
    assert VERSION=='3.11'
    assert sshupdates.prepare_version_restore.__kwdefaults__['source_version']==VERSION
    assert firmwarefactory.OFFICIAL_VERSION=='2.01'


def test_recovery_preserves_official_201_header_and_body(tmp_path,monkeypatch):
    from types import SimpleNamespace
    header=bytearray(512);header[0x20:0x22]=b'\x01\x02'
    original=bytes(header)+b'original-body-with-settings-and-resources'
    def decode(source,target):Path(target).write_bytes(original)
    monkeypatch.setattr(firmwarefactory,'decode',decode)
    monkeypatch.setattr(firmwarefactory,'tools',lambda:(SimpleNamespace(FdatHeader=SimpleNamespace(size=512)),))
    signing=[]
    monkeypatch.setattr(firmwarefactory,'finish_signing',lambda *args:signing.append(args))
    out=tmp_path/'recovery';job=tmp_path/'job';job.mkdir()
    report=firmwarefactory.build(dict(workspace=str(out),sony_firmware='owner-source.DAT'),job)
    actual=(out/'candidate.FDAT.UNSIGNED.bin').read_bytes()
    assert actual==original
    assert (out/'original.FDAT.private.bin').read_bytes()==original
    assert report['update_header_version']=='2.01'and report['same_version_card_update_verified']is False
    assert len(signing)==1


def test_all_real_default_templates_keep_normal_output_and_reject_missing_property(tmp_path):
    from pmca.backup import BackupFile
    source=Path('E:/CodexData/a7c2-fixed-look-static-20261109/firmware-restart-02/original.FDAT.private.bin')
    manifest=source.parent/'baseline/baseline.private.json'
    if not source.is_file()or not manifest.is_file():pytest.skip('Private original C2 template inputs unavailable')
    wanted=[{int(k):bytes.fromhex(v)for k,v in row.items()}for row in json.loads(manifest.read_text(encoding='utf-8'))['wanted']]
    with source.open('rb')as f:
        header=f.read(512);f.seek(struct.unpack_from('<I',header,0x30)[0])
        with tarfile.open(fileobj=f,mode='r:')as t:
            templates={m.name:t.extractfile(m).read()for m in t if m.isfile()and m.name.startswith('0110_backup/')and m.name.endswith('.bin')}
    def records(raw):
        result=[];at=0
        while (at:=raw.find(b'BK4\0',at))>=0:
            try:result.append(dict(BackupFile(io.BytesIO(raw[at-12:])).listProperties()))
            except Exception:pass
            at+=4
        return result
    base=next(v for k,v in templates.items()if k.endswith('/CX89700_ALLLANG.bin'))
    reference=records(base)
    before=Path('E:/CodexData/a7c2-card-preflight-20261112/before/firmwarelocal.py')
    node=next(n for n in ast.parse(before.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)and n.name=='patch_defaults')
    namespace={'io':io};exec(compile(ast.Module(body=[node],type_ignores=[]),str(before),'exec'),namespace)
    # Existing normal output must remain byte-for-byte identical across 12 templates.
    for name,raw in templates.items():
        assert firmwarelocal.patch_defaults(raw,wanted,reference)==namespace['patch_defaults'](raw,wanted,reference),name
    raw=next(v for k,v in templates.items()if k.endswith('/CX89700_E38.bin'))
    s=io.BytesIO(raw);b=BackupFile(s);prop=b.getProperty(0x02cf1289)
    b._writePropertyTable(0x02cf1289,prop.attr,0xffffffff);b.updateChecksum()
    with pytest.raises(ValueError,match='missing or ambiguous'):
        firmwarelocal.patch_defaults(s.getvalue(),[{0x02cf1287:b'\x0a',0x02cf1289:b'\x0b'},{}],reference)
