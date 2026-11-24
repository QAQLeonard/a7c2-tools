"""Actual option composition and command compilation; no device or screenshots."""
def run(request_path):
    import itertools,json,shutil,sys
    from pathlib import Path
    from PySide6 import QtWidgets as W
    from desktopapp import cameraapi,firmwarefeatures,firmwarelocal,window
    from desktopapp.paths import ROOT,write_json
    from desktopapp.worker import setup_runtime
    setup_runtime();sys.path.insert(0,str(ROOT/'src/shutter_sound'))
    from looktool import device_layout,fixedbankcode,fixedlooks,photoio
    from looktool.devicesession import modules
    request=json.loads(Path(request_path).read_text(encoding='utf-8'))
    folder=Path(request['folder']);folder.mkdir(parents=True,exist_ok=False)
    app=W.QApplication.instance()or W.QApplication([])
    view=window.Window(demo=True)
    checks=[]
    try:
        view.timer.stop();view.select_page('firmware')
        view.local_looks.setChecked(False)
        args=view.firmware_args()
        assert not args['custom_looks']and not args['ssh']and not args['looks']and args['preset_pack']is None
        assert args['sound']and args['vertical']and args['update_version']=='3.11'
        view.local_custom_looks.setChecked(True)
        assert view.firmware_args()['looks']==[]
        view.local_looks.setChecked(True)
        assert view.local_ssh.isEnabled()
        view.local_presets.setChecked(True)
        assert view.firmware_args()['preset_pack']
        checks.append('GUI_unchecked_looks_clears_payloads_and_SSH_without_disabling_other_features')
        view.local_sound.setChecked(False);view.local_custom_sound.setChecked(True)
        assert view.firmware_args()['custom_sound']is None
        checks.append('GUI_disabled_sound_ignores_stale_custom_selection')
    finally:view.process=None;view.close()

    originals=Path(request['originals']);current={}
    _,_,ext2,fat=firmwarelocal.tools()
    for filename,reader,entry_name,key in (('usr.img',ext2.readExt2,'/lib/appFw.so','appFw.so'),
                                         ('cp.img',fat.readFat,'/cpapp-b.bin','cpapp-b.bin')):
        with (originals/filename).open('rb')as image:
            for row in reader(image):
                if row.path==entry_name:
                    current[key]=firmwarelocal.stream_bytes(row.contents);break
        assert key in current
    for key in ('settings-ram.bin','settings-saved.bin'):
        current[key]=(Path(request['baseline'])/key).read_bytes()
    records=modules()[1].backup_records(current['settings-ram.bin'])
    results=[]
    previous=None
    if request.get('prior_report'):
        previous=json.loads(Path(request['prior_report']).read_text(encoding='utf-8'))
        assert previous['passed']and len(previous['feature_combinations'])==16
        results=previous['feature_combinations'];checks.extend(previous['checks'])
    for bits in (()if previous else itertools.product((False,True),repeat=4)):
        flags=dict(zip(('fl23','whitebalance','sound','vertical'),bits))
        target,wanted,selected,files,report=firmwarefeatures.compose(current,records,
            dict(flags,custom_looks=False,ssh=False,looks=[],workspace=str(folder)))
        assert not selected and not report['fixed_creative_looks']and not report['fixed_look_storage']
        assert device_layout.structural_ap(target['appFw.so'])['mask']==0
        assert not fixedlooks.present(target['appFw.so'])and not fixedbankcode.present(target['cpapp-b.bin'])
        assert not photoio.present(target['cpapp-b.bin'])
        assert not any('custom-shutter'in name for name in files)
        assert bool(files)==flags['vertical']
        output=folder/('combination-'+''.join(str(int(n))for n in bits))
        binary=cameraapi.build(target,output,request['zig'])
        assert binary.read_bytes()[:4]==b'\x7fELF'
        results.append(dict(flags,API_compiled=True,custom_slots=[],fixed_bank=False))
        print('OPTION_COMPILED',bits,flush=True)
    checks.append('all_16_no_custom_look_feature_combinations_compose_and_compile')

    # Existing full native/static builds must still compile after shared readback changes.
    if not previous:
        prior=Path(request['fixed_baseline'])
        binary=cameraapi.build({name:(prior/name).read_bytes()for name in ('appFw.so','cpapp-b.bin')},
                               folder/'default-six-api',request['zig'])
        assert binary.read_bytes()[:4]==b'\x7fELF'
    checks.append('existing_fixed_six_look_API_still_compiles')

    target,wanted,selected,files,report=firmwarefeatures.compose(current,records,
        dict(custom_looks=False,ssh=False,looks=[],sound=True,vertical=False,
             workspace=str(folder/'custom-sound-no-looks'),custom_sound=dict(
                 source=request['audio'],start=0,duration=.08,selection='both')))
    assert not selected and report['custom_shutter_sound']['kinds']==[1,2,3]
    assert '/share/avsystemsound/custom.txt'in files
    binary=cameraapi.build(target,folder/'custom-sound-api',request['zig'])
    assert binary.read_bytes()[:4]==b'\x7fELF'
    checks.append('custom_mechanical_and_electronic_sound_compiles_without_custom_looks')

    # Invalid UI header must fail before removing a previous good result.
    output=folder/'invalid-version';output.mkdir();(output/'BODYDATA.DAT').write_bytes(b'previous result')
    try:firmwarelocal.build(dict(workspace=str(output),sony_firmware='unused',custom_looks=False,
                                update_version='3.1.0'),folder/'unused-job')
    except ValueError as exc:assert 'Sony'in str(exc)
    else:raise AssertionError('invalid header accepted')
    assert (output/'BODYDATA.DAT').read_bytes()==b'previous result'
    checks.append('invalid_version_preserves_previous_output')
    source=folder/'source-protection';(source/'api').mkdir(parents=True)
    from desktopapp import presets
    look=source/'api/user.a7look';shutil.copyfile(presets.catalog()[0]['path'],look)
    before=look.read_bytes()
    try:firmwarelocal.build(dict(workspace=str(source),sony_firmware='unused',custom_looks=True,
                                looks=[dict(slot=1,path=str(look))]),folder/'unused-job')
    except ValueError:pass
    else:raise AssertionError('source inside output removed')
    assert look.read_bytes()==before
    checks.append('API_output_cleanup_preserves_selected_input_on_conflict')
    cleanup=folder/'cleanup';(cleanup/'api').mkdir(parents=True)
    (cleanup/'api/a7c2-api').write_bytes(b'intermediate')
    (cleanup/'BODYDATA.DAT').write_bytes(b'final')
    firmwarelocal.finish_output(cleanup,dict(signed=True),folder/'cleanup-job')
    assert [p.name for p in cleanup.iterdir()]==['BODYDATA.DAT']
    checks.append('successful_no_SSH_output_removes_API_intermediates')
    report=dict(passed=True,version='3.11',checks=list(dict.fromkeys(checks)),feature_combinations=results,
                prior_option_report=request.get('prior_report'),
                camera_io=False,screenshots=False,new_validation_hashes=False)
    write_json(request['report'],report)
    return report
