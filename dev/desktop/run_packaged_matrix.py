"""Run release composition tests inside either native distribution."""
import argparse,json,math,os,struct,subprocess,urllib.request,wave
import sys
from pathlib import Path

OFFICIAL='https://support.d-imaging.sony.co.jp/download/NEX/uua3b90658/BODYDATA.DAT?fm=jp?fm=jp&upid=&s_tc='


def run(app,workspace,source=None):
    folder=Path(workspace).resolve();folder.mkdir(parents=True,exist_ok=False)
    if source is None:
        source=folder/'official-BODYDATA.DAT'
        request=urllib.request.Request(OFFICIAL,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=120)as src,source.open('xb')as dst:
            import shutil
            shutil.copyfileobj(src,dst,1<<20)
    audio=folder/'clip.wav'
    with wave.open(str(audio),'wb')as stream:
        stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(24000)
        stream.writeframes(b''.join(struct.pack('<h',round(7000*math.sin(i*2*math.pi*880/24000)))for i in range(21600)))
    request=folder/'request.json'
    request.write_text(json.dumps(dict(output=str(folder/'cases'),official=str(Path(source).resolve()),
             audio=str(audio),duration=.9,compile_api=False,external_native=os.name=='nt')),encoding='utf-8')
    env=dict(os.environ,A7C2_RELEASE_MATRIX=str(request),QT_QPA_PLATFORM='offscreen',
             A7C2_DESKTOP_DATA=str(folder/'app-data'))
    with(folder/'console.log').open('wb')as log:
        done=subprocess.run([str(Path(app).resolve()),'--color-self-test',str(folder/'result.json')],
             stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=1800)
    if done.returncode:
        print((folder/'console.log').read_text(encoding='utf-8',errors='replace')[-8000:])
        raise RuntimeError('Packaged composition matrix failed: '+str(done.returncode))
    result=json.loads((folder/'result.json').read_text())
    assert result['passed']and result['count']==54
    if os.name=='nt':
        # Keep the Windows GUI runtime and Unicorn's native exception handling
        # in separate processes. Execute the exact CP bytes saved by the app.
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src/looks'))
        from looktool import fixedbank
        from firmware_matrix import gamma_pointers
        count=0
        for row in result['cases']:
            if 'native_CP_source'not in row:continue
            cp=Path(row['native_CP_source']).read_bytes()
            count+=gamma_pointers(cp,fixedbank.parse(fixedbank.extract_cp(cp)))
        result['external_native_gamma_pointer_checks']=count
        (folder/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(version=result['version'],cases=result['count'],camera_io=False)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--app',required=True,type=Path);p.add_argument('--workspace',required=True,type=Path)
    p.add_argument('--source',type=Path)
    a=p.parse_args();run(a.app,a.workspace,a.source)
