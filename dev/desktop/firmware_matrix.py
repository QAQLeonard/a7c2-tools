"""Offline release coverage using supplied original images; no camera access."""
import itertools,json,stat,struct,time
from pathlib import Path


def run(request_path):
    import sys
    from desktopapp.paths import ROOT
    sys.path.insert(0,str(ROOT/'src/shutter_sound'))
    from desktopapp import VERSION,firmwarelocal,firmwarefeatures,presets,cameraapi
    from desktopapp.worker import setup_runtime
    setup_runtime()
    from looktool import fixedbank,fixedbankcode,photoformat,photofull,lookfile
    from looktool.nameworker import filenames
    from looktool.devicesession import modules
    import targeted_sound
    request=json.loads(Path(request_path).read_text(encoding='utf-8'))
    out=Path(request['output']);out.mkdir(parents=True,exist_ok=bool(request.get('resume')))
    if request.get('official'):
        import tarfile,shutil
        inputs=out/'originals';inputs.mkdir()
        decoded=inputs/'original.FDAT.private.bin'
        firmwarelocal.decode(request['official'],decoded)
        fdat=firmwarelocal.tools()[0]
        with decoded.open('rb')as stream:
            contents=fdat.readFdat(stream)
            with tarfile.open(fileobj=contents.firmware,mode='r:')as archive:
                for key in ('usr','cp'):
                    dest=inputs/(key+'.img')
                    with archive.extractfile(firmwarelocal.IMAGE_NAMES[key])as src,dest.open('xb')as dst:shutil.copyfileobj(src,dst,1<<20)
                    request[key]=str(dest)
                member=next(m for m in archive.getmembers()if m.name.endswith('/CX89700_ALLLANG.bin'))
                settings=inputs/'settings.bin';settings.write_bytes(archive.extractfile(member).read())
                request['settings']=str(settings)
    _,_,ext2,fat=firmwarelocal.tools();current={}
    for file,reader in ((request['usr'],ext2.readExt2),(request['cp'],fat.readFat)):
        with Path(file).open('rb')as stream:
            for entry in reader(stream):
                if not stat.S_ISREG(entry.mode):continue
                path=entry.path.lstrip('/');base=path.rsplit('/',1)[-1]
                if path=='lib/appFw.so':key='appFw.so'
                elif path=='cpapp-b.bin':key=path
                elif path.startswith('share/app/')and base in filenames():key='resources/'+base
                elif path.startswith('share/app/')and base in {f'image_{i:02d}_32_IPSX.uxc'for i in range(3)}:key='images/'+base
                else:continue
                current[key]=firmwarelocal.stream_bytes(entry.contents)
    current['settings-ram.bin']=current['settings-saved.bin']=Path(request['settings']).read_bytes()
    records=modules()[1].backup_records(current['settings-ram.bin'])
    defaults=[dict(slot=i,path=str(row['path']))for i,row in enumerate(presets.catalog(),1)]
    legacy_dir=Path(request['legacy'])if request.get('legacy')else out/'legacy-fixtures'
    if not request.get('legacy'):
        from looktool import device_layout,photobasis
        cp=device_layout.replace(current['appFw.so'],current['cpapp-b.bin'],{1:bytes(1215)},hash_checks=False,transitions=False)[2]['cpapp-b.bin']
        basis=photoformat.extract_bank(cp,records[1][0x02a40001].data,records[1][0x02a4000d].data,
            gamma_table_va=0x1209480,regular_row=0,still_row=10,color_parameter=0)[0]
        legacy_dir.mkdir()
        for i,row in enumerate(defaults,1):
            doc=lookfile.read(row['path']);doc.pop('edit_native',None)
            doc.update(schema=lookfile.SCHEMA,method='Offline release regression fixture',
                       native_photo=photobasis.pack(basis,tone=[i*8,0,0])[1])
            lookfile.validate(doc);lookfile.writer_document(doc)
            (legacy_dir/f'slot{i}.a7look').write_text(json.dumps(doc),encoding='utf-8')
    legacy=[dict(slot=i,path=str(legacy_dir/f'slot{i}.a7look'))for i in range(1,7)]
    mixed=legacy[:];mixed[3]=defaults[3]
    datasets={'none':None,'neutral':[],'default-six':defaults,'legacy-six':legacy,
              'mixed-six':mixed,'single-legacy':[dict(slot=2,path=legacy[1]['path'])]}
    cases=[]
    for name in datasets:
        for audio in (None,'electronic','mechanical','both'):
            cases.append((name,audio,(True,True,True,True)))
    # Cross the remaining feature switches with both predecessor families.
    for name in ('default-six','legacy-six'):
        for flags in itertools.product((False,True),repeat=4):
            if flags!=(True,True,True,True):cases.append((name,None,flags))
    results=json.loads((out/'progress.json').read_text())if request.get('resume')and(out/'progress.json').exists()else[]
    for number,(name,audio,bits)in enumerate(cases,1):
        started=time.monotonic();looks=datasets[name]
        flags=dict(zip(('fl23','whitebalance','sound','vertical'),bits))
        label=f'{number:02d}-{name}-{audio or "factory"}-'+''.join(str(int(v))for v in bits)
        if any(row['case']==label for row in results):continue
        workspace=out/label;attempt=1
        while workspace.exists():
            attempt+=1;workspace=out/(label+f'-attempt{attempt}')
        args=dict(flags,custom_looks=looks is not None,ssh=looks is not None,
                  looks=looks or [],workspace=str(workspace))
        if audio:args['custom_sound']=dict(source=request['audio'],start=request.get('start',0),
             duration=request.get('duration',.9),selection=audio)
        print('COMPOSE_START',label,flush=True)
        target,wanted,selected,files,meta=firmwarefeatures.compose(current,records,args)
        print('COMPOSE_DONE',label,flush=True)
        cp=target['cpapp-b.bin'];ap=target['appFw.so'];kinds=[]
        for at,raw in fixedbankcode.NATIVE_GAMMA_HOOKS.items():assert cp[at:at+len(raw)]==raw,(label,hex(at))
        if looks is not None:
            fixedbankcode.inspect(cp);parsed=fixedbank.parse(fixedbank.extract_cp(cp))
            kinds=[row[2]for row in parsed['entries']]
            if name=='legacy-six'or name=='neutral':assert kinds==[1]*6
            if name=='default-six':assert kinds==[2]*6
            if name=='mixed-six':assert kinds==[1,1,1,2,1,1]
            if name=='single-legacy':assert kinds==[0,1,0,0,0,0]
            pointers=0 if request.get('external_native')else gamma_pointers(cp,parsed)
            print('GAMMA_DONE',label,flush=True)
        else:
            assert meta['fixed_look_storage']is None;pointers=0
        if flags['sound']:
            assert all(ap[at:at+len(after)]==after for at,before,after in targeted_sound.windows(ap))
        custom=files.get('/share/avsystemsound/custom.txt')
        if audio:
            parsed_sound=targeted_sound.decode(custom)
            expected={'electronic':{3},'mechanical':{1,2,10,11,12,13,14,15},
                      'both':{1,2,3,10,11,12,13,14,15}}[audio]
            assert set(parsed_sound)==expected
            assert meta['custom_shutter_sound']['encoded_bytes']<=51200
        else:assert custom is None
        api=False
        if number<=24 and request.get('compile_api',False):
            binary=cameraapi.build(target,out/label/'api',request.get('zig'))
            assert binary.read_bytes()[:4]==b'\x7fELF';api=True
        row=dict(case=label,kinds=kinds,flags=flags,audio=audio,
          native_gamma_pointers=pointers,API_compiled=api,seconds=round(time.monotonic()-started,3))
        if looks is not None and request.get('external_native'):
            row['native_CP_source']=str(workspace/'fixed-look-source/cpapp-b.fixed.bin')
        results.append(row)
        (out/'progress.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        print('MATRIX_PASSED',label,flush=True)
    report=dict(passed=True,version=VERSION,cases=results,count=len(results),
      native_gamma_pointer_checks=sum(r['native_gamma_pointers']for r in results),
      API_compiles=sum(r['API_compiled']for r in results),camera_io=False,physical_boot=False)
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def gamma_pointers(cp,parsed):
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
    from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R6,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
    base=0x108000;u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
    u.mem_map(base,0x1200000);u.mem_write(base,cp)
    u.mem_map(0x02700000,0x10000);u.mem_write(0x02700000,cp[0xa400:0xb400])
    total=struct.unpack_from('<I',cp,0x1103000)[0]
    u.mem_map(0x02a80000,0x80000);u.mem_write(0x02a80000,cp[0x1103000:0x1103000+total])
    scratch=0x08000000;u.mem_map(scratch,0x20000);count=0
    for slot,domain,column in itertools.product(range(6),range(2),range(7)):
        info=scratch+0x1000
        u.mem_write(info+16,struct.pack('<I',50+slot*2+domain));u.mem_write(info+24,bytes([column]))
        for reg,value in ((UC_ARM_REG_R0,scratch+0x4000),(UC_ARM_REG_R1,scratch+0x5000),
            (UC_ARM_REG_R2,info),(UC_ARM_REG_R3,scratch+0x6000),
            (UC_ARM_REG_SP,scratch+0x1f000),(UC_ARM_REG_LR,scratch+0x10001)):
            u.reg_write(reg,value)
        u.emu_start(0x42b44d,0x42b478,count=1000)
        expected=struct.unpack_from('<I',cp,0x1103000+0xa00+slot*16+4)[0]+912+(domain*7+column)*576
        assert u.reg_read(UC_ARM_REG_PC)==0x42b478 and u.reg_read(UC_ARM_REG_R6)==expected
        record=parsed['entries'][slot][1];at=912+(domain*7+column)*576
        assert bytes(u.mem_read(expected,576))==record[at:at+576]
        count+=1
    return count


if __name__=='__main__':
    import sys
    run(sys.argv[1])
