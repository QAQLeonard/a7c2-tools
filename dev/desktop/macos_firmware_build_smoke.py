"""Run the packaged firmware worker with official input; never opens a camera."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def run(app,source,workspace,report,*,sound_both=False,sound_selection=None,look_dir=None):
    workspace=Path(workspace).resolve();workspace.mkdir(parents=True,exist_ok=False)
    output=workspace/'generated';job=workspace/'job';job.mkdir()
    arguments=dict(sony_firmware=str(Path(source).resolve()),workspace=str(output),
        update_version='3.11',fl23=True,whitebalance=True,sound=True,ssh=True,
        custom_looks=True,vertical=True,precapture=False,voice_cleanup=True,
        automatic_identity=True,looks=[],custom_sound=None,preset_pack='default-six-v1')
    if look_dir:
        arguments['preset_pack']=None
        arguments['looks']=[dict(slot=i,path=str(Path(look_dir).resolve()/f'slot{i}.a7look'))for i in range(1,7)]
    if sound_both or sound_selection:
        import math,struct,wave
        clip=workspace/'custom-sound-test.wav'
        with wave.open(str(clip),'wb') as output_wav:
            output_wav.setnchannels(1);output_wav.setsampwidth(2);output_wav.setframerate(24000)
            output_wav.writeframes(b''.join(struct.pack('<h',round(6000*math.sin(i*2*math.pi*880/24000))) for i in range(4800)))
        arguments['custom_sound']=dict(source=str(clip),start=0,duration=.2,selection=sound_selection or'both')
    request=job/'request.private.json'
    request.write_text(json.dumps(dict(action='firmware_build',arguments=arguments,job_dir=str(job))),encoding='utf-8')
    env=dict(os.environ,A7C2_DESKTOP_DATA=str(workspace/'app-data'))
    with (workspace/'worker-console.log').open('w',encoding='utf-8') as log:
        done=subprocess.run([str(Path(app).resolve()),'--worker',str(request)],env=env,
                            stdout=log,stderr=subprocess.STDOUT,timeout=1800)
    status_path=job/'status.private.json'
    status=json.loads(status_path.read_text()) if status_path.is_file() else {}
    if done.returncode or status.get('phase')!='SUCCEEDED':
        for path in (workspace/'worker-console.log',job/'worker.log'):
            if path.is_file():print(path.read_text(encoding='utf-8',errors='replace')[-7000:])
        raise RuntimeError('Packaged Mac firmware_build failed: '+str(status.get('error',done.returncode)))
    result=status['result']
    assert result['signed'] and result['signature_validation']['plaintext_byte_readback']
    assert result['ssh'] and result['features']['sound'] and result['features']['vertical']
    assert result['filter_slots']==[1,2,3,4,5,6] and result['menu_icon_slots']==[1,2,3,4,5,6]
    if sound_both:
        custom=result['custom_shutter_sound']
        assert custom['selection']=='both' and custom['kinds']==[1,2,3,10,11,12,13,14,15]
    target=Path(result['candidate'])
    assert target==output/'BODYDATA.DAT' and target.stat().st_size>0
    summary=dict(version='3.11',action='firmware_build',phase='SUCCEEDED',
        signed=True,plaintext_readback=True,ssh=True,default_looks=6,icons=True,
        sound=True,vertical=True,firmware_bytes=target.stat().st_size,
        camera_io=False,screenshots=False,firmware_included_in_artifact=False)
    if sound_both:summary['custom_shutter_sound']='both'
    if sound_selection:summary['custom_shutter_sound']=sound_selection
    if look_dir:summary.update(default_looks=0,custom_looks=6)
    Path(report).write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app',required=True,type=Path)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--workspace',required=True,type=Path)
    parser.add_argument('--report',required=True,type=Path)
    parser.add_argument('--sound-both',action='store_true')
    parser.add_argument('--sound-selection',choices=['electronic','mechanical','both'])
    parser.add_argument('--look-dir',type=Path)
    args=parser.parse_args();run(args.app,args.source,args.workspace,args.report,sound_both=args.sound_both,
                               sound_selection=args.sound_selection,look_dir=args.look_dir)
