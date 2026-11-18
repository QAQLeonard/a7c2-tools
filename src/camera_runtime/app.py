"""A7C II 2.01 preview installer. Per-body backup, explicit phases, no retries."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import struct
import core

def event(message):print(message,flush=True)

class Job:
    def __init__(self,workspace):
        self.root=Path(workspace).resolve();self.state_path=self.root/'state.json'
    def save(self,phase,**values):
        self.state.update(values);self.state['phase']=phase
        core.save_json(self.state_path,self.state)
    def audit(self,step,**values):
        row={'time':datetime.now().isoformat(),'step':step,**values}
        self.state.setdefault('journal',[]).append(row);core.save_json(self.state_path,self.state)
    def load(self):
        core.assets();self.state=core.read_json(self.state_path)
        if self.state.get('format')!=1 or self.state.get('model')!=core.MODEL:raise ValueError('Not a valid body workspace')
        for name in self.state['backup_files']:
            if (self.root/'original'/name).read_bytes()!=(Path(self.state['backup_copy'])/name).read_bytes():
                raise ValueError('The two backup copies differ: '+name)
        core.backup_records((self.root/'original/backup.private.bin').read_bytes())
        if 'compatibility' in self.state:
            import compat
            compat.validate(self.root,self.state)
        return self
    def module(self,session,name,mode=None,byte_build=None):
        blob=(core.BASE/'assets'/f'{name}.so').read_bytes()
        dynamic=name=='installer' and 'compatibility' in self.state
        if dynamic:
            import compat
            compat.validate(self.root,self.state)
            if self.state['compatibility']['already_enabled']:raise ValueError('Installer must not run when already enabled')
            if 'byte_builds' in self.state['compatibility']:
                if byte_build is None:
                    return [self.module(session,name,mode,build) for build in self.state['compatibility']['byte_builds']]
                blob=Path(byte_build['path']).read_bytes()
            else:blob=(self.root/'compat-worker/program.so').read_bytes()
        result={'installer':'a7c2.install.result','probe':'a7c2.probe.result',
                'wbi':'a7c2.wbi.result','runtime':'a7c2.runtime.result'}[name]
        request={'installer':('a7c2.install.request',b'A7INS001'),
                 'wbi':('a7c2.wbi.request',b'A7WBI001')}.get(name)
        names=['libJit.so','a7c2-preview-staged.so',result]
        if name=='runtime':names.append('a7c2.probe.result')
        if request:names.append(request[0])
        for item in names:
            if session.read('/tmp/jiritsu/'+item,True) is not None:
                raise RuntimeError('A previous temporary file exists; save it and confirm the result first, do not simply retry: '+item)
        if session.read('/tmp/jiritsu/../../etc/ld.so.preload',True):raise RuntimeError('Existing preload configuration found; stopping')
        created=[];launched=False
        try:
            created.append('a7c2-preview-staged.so');session.temp(created[-1],blob)
            if session.read('/tmp/jiritsu/'+created[-1])!=blob:raise RuntimeError('Temporary module readback mismatch')
            if request:
                contents=struct.pack('<8sII',request[1],mode,0)
                created.append(request[0]);session.temp(request[0],contents)
                if session.read('/tmp/jiritsu/'+request[0])!=contents:raise RuntimeError('Run-mode readback mismatch')
            self.audit('native_about_to_run',module=name,mode=mode)
            created.extend(['libJit.so',result])
            if name=='runtime':created.append('a7c2.probe.result')
            launched=True
            session.temp('libJit.so',blob)
            raw=session.read('/tmp/jiritsu/'+result)
            dest=self.root/'evidence'/f'{datetime.now():%Y%m%d-%H%M%S-%f}-{name}.bin'
            dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
            if dynamic:
                if byte_build is not None:
                    from looktool.checkpointworker import program_report
                    parsed=program_report(raw,mode,byte_build)
                else:
                    from compat import modules
                    parsed=modules()[3].validate_worker_report(raw,mode,self.state['compatibility']['build']['contract'])
            else:parsed=core.parse_native(name,raw,mode)
            self.audit('native_verified',module=name,mode=mode,result=parsed)
            return parsed
        except BaseException:
            if launched:session.healthy=False
            raise
        finally:
            for item in reversed(list(dict.fromkeys(created))):
                if not session.healthy:
                    self.audit('temporary_cleanup_pending',name=item);continue
                if session.read('/tmp/jiritsu/'+item,True) is not None:session.temp(item,remove=True)
                if session.read('/tmp/jiritsu/'+item,True) is not None:raise RuntimeError('Temporary file cleanup incomplete')
    def prepare(self,second,firmware_version=core.VERSION):
        from transport import Session
        core.assets()
        if firmware_version!=core.VERSION:raise ValueError('FL23 supports firmware 2.01 only; enter the version shown on the camera version page')
        if self.root.exists() and any(self.root.iterdir()):raise ValueError('Choose a new, empty workspace folder; keep the old records')
        second=Path(second).resolve()
        if second==self.root or self.root in second.parents or second in self.root.parents:raise ValueError('The second backup must use a separate folder; the two folders must not contain each other')
        if second.exists() and any(second.iterdir()):raise ValueError('The second backup folder must be empty')
        self.root.mkdir(parents=True,exist_ok=True);second.mkdir(parents=True,exist_ok=True)
        (self.root/'original').mkdir();(self.root/'candidate').mkdir()
        self.state={'format':1,'model':core.MODEL,'version':firmware_version,'version_source':'user-camera-version-screen','phase':'preparing',
                    'backup_copy':str(second),'backup_files':{},'journal':[]}
        self.save('preparing')
        with Session() as session:
            self.state['identity']=session.identity
            event('A7C II detected; backing up the original programs and the settings of this camera.')
            backup=session.call(session.camera.getBackupPresetData,True);records=core.backup_records(backup)
            originals={}
            for chip,name,path in [(1,core.PROGRAMS[1],'/cp/cpapp-b.bin'),(0,core.PROGRAMS[0],'/usr/lib/appFw.so')]:
                event('Reading full '+name)
                data=session.read('/tmp/jiritsu/../..'+path)
                originals[name+'.bin']=data
            originals['backup.private.bin']=backup
            for key in core.CP_KEYS:
                data=session.cp_read(key)
                if data!=records[1][key].data:raise ValueError('Native colour readback does not match the body backup')
                originals[f'unit-{key:08x}.bin']=data
            # Capture the initial rollback point before building candidates.
            # A later LUT job must not invalidate this independent archive.
            import compat
            compat.modules()
            from looktool import checkpoint
            saved=session.call(session.camera.getBackupPresetData,False)
            values=checkpoint.capture(session,{name:originals[name+'.bin'] for name in core.PROGRAMS},backup,saved)
            archive=self.root/'original/checkpoint.private.zip'
            checkpoint.write(archive,values,session.identity,provenance={'type':'fl23-prepare-before-changes'})
            checkpoint.copy(archive,second/'checkpoint.private.zip')
            self.state['checkpoint']=str(second/'checkpoint.private.zip')
            for name,data in originals.items():
                for parent in [self.root/'original',second]:
                    target=parent/name;target.write_bytes(data)
                    if target.read_bytes()!=data:raise ValueError('Backup write-back verification mismatch')
                self.state['backup_files'][name]=len(data)
            self.save('backups_verified')
            self.state['compatibility']=compat.prepare(self.root,originals['appFw.so.bin'],originals['cpapp-b.bin.bin'],firmware_version)
            self.audit('version_and_patch_positions_checked',**self.state['compatibility']['identity'])
            enabled=self.state.get('compatibility',{}).get('already_enabled',False)
            for i,key in enumerate(core.AP_KEYS):
                expected=bytes([10+i]) if enabled else b'\0'
                if session.call(session.camera.readBackup,key)!=expected or records[0][key].data!=expected:
                    raise ValueError('Reserved slot is already in use; this preview refuses to overwrite it')
            units=(originals['unit-02a40001.bin'],originals['unit-02a4000d.bin'])
            if enabled:
                compat.validate_enabled_colors(*units);merged=units
            else:merged=core.merge_colors(*units)
            for key,data in zip(core.CP_KEYS,merged):(self.root/'candidate'/f'unit-{key:08x}.bin').write_bytes(data)
            self.save('backups_verified')
            self.module(session,'probe')
            if not enabled:
                self.module(session,'installer',0)
                self.module(session,'wbi',0)
        self.save('prepared')
        if enabled:event('Confirmed FL2/FL3 are already enabled; LUTs, names and custom recipes kept, nothing rewritten. Run verify to check the loaded state.')
        else:event('Backup, candidate and read-only camera check complete. Firmware and saved shooting settings have not been changed yet.')
    def units(self):
        originals={k:(self.root/'original'/f'unit-{k:08x}.bin').read_bytes() for k in core.CP_KEYS}
        merged=core.merge_colors(originals[core.CP_KEYS[0]],originals[core.CP_KEYS[1]])
        return originals,dict(zip(core.CP_KEYS,merged))
    def files(self,session,after):
        for chip,name,path in [(1,core.PROGRAMS[1],'/cp/cpapp-b.bin'),(0,core.PROGRAMS[0],'/usr/lib/appFw.so')]:
            event('Full readback '+name)
            data=session.read('/tmp/jiritsu/../..'+path)
            folder=self.root/'readback';folder.mkdir(exist_ok=True)
            stamp=f'{datetime.now():%Y%m%d-%H%M%S-%f}-{name}'
            (folder/stamp).write_bytes(data)
            original=(self.root/'original'/(name+'.bin')).read_bytes()
            if not after:expected=original
            elif 'compatibility' in self.state:expected=(self.root/'candidate'/name).read_bytes()
            else:expected=core.patch_program(original,chip)
            if data!=expected:raise ValueError('Full program readback mismatch; stopping further operations')
        self.audit('host_full_file_readback_verified',after=after)
    def settings(self,session,restore=False):
        originals,merged=self.units();target=originals if restore else merged
        desired=dict(zip(core.AP_KEYS,[b'\0',b'\0'] if restore else [b'\x0a',b'\x0b']))
        before_raw=session.call(session.camera.getBackupPresetData,True);before=core.backup_records(before_raw)
        folder=self.root/'evidence';folder.mkdir(exist_ok=True)
        (folder/f'{datetime.now():%Y%m%d-%H%M%S-%f}-settings-before.private.bin').write_bytes(before_raw)
        current_cp={k:session.cp_read(k) for k in core.CP_KEYS}
        current_ap={k:session.call(session.camera.readBackup,k) for k in core.AP_KEYS}
        for key in core.CP_KEYS:
            accepted=[originals[key],merged[key]] if restore else [originals[key]]
            if current_cp[key] not in accepted or before[1][key].data!=current_cp[key]:raise ValueError('CP settings state unknown; refusing to write')
        for i,key in enumerate(core.AP_KEYS):
            accepted=[b'\0',bytes([10+i])] if restore else [b'\0']
            if current_ap[key] not in accepted or before[0][key].data!=current_ap[key]:raise ValueError('AP settings state unknown; refusing to write')
        for key in core.CP_KEYS:
            if current_cp[key]==target[key]:continue
            self.audit('about_to_write_cp',key=hex(key));session.cp_write(key,target[key])
            if session.cp_read(key)!=target[key]:raise ValueError('CP readback failed')
        if any(current_cp[k]!=target[k] for k in core.CP_KEYS):
            self.audit('about_to_save_cp');session.call(session.camera.saveBackup,0x02a4)
        for key in core.AP_KEYS:
            if current_ap[key]==desired[key]:continue
            self.audit('about_to_write_ap',key=hex(key));session.ap_write(key,desired[key])
            if session.call(session.camera.readBackup,key)!=desired[key]:raise ValueError('AP binding readback failed')
        if any(current_ap[k]!=desired[k] for k in core.AP_KEYS):
            self.audit('about_to_save_ap');session.call(session.camera.saveBackup,0x02cf)
        after_raw=session.call(session.camera.getBackupPresetData,True)
        stored_raw=session.call(session.camera.getBackupPresetData,False)
        (folder/f'{datetime.now():%Y%m%d-%H%M%S-%f}-settings-after.private.bin').write_bytes(after_raw)
        (folder/f'{datetime.now():%Y%m%d-%H%M%S-%f}-settings-stored.private.bin').write_bytes(stored_raw)
        expected={(0,k):v for k,v in desired.items()};expected.update({(1,k):v for k,v in target.items()})
        preservation=core.verify_preservation(before,core.backup_records(after_raw),expected)
        stored=core.backup_records(stored_raw)
        for (chip,key),value in expected.items():
            if stored[chip][key].data!=value:raise ValueError('Readback after save mismatch')
        self.audit('settings_storage_verified',restore=restore,**preservation)
    def install(self,battery=None,*,power_confirmed=False):
        from transport import Session
        self.load()
        if self.state['phase']!='prepared':raise ValueError('Run prepare first; re-running is not allowed while the state is unknown')
        if self.state.get('compatibility',{}).get('already_enabled'):
            event('Prepare already confirmed FL2/FL3 are present; nothing was installed. Run verify.');return
        import compat
        event('Note: '+compat.WARNING)
        from looktool.power import require_power
        self.state['power_confirmation']=require_power(battery,confirmed=power_confirmed)
        with Session(self.state['identity']) as session:
            # Recheck every per-body target before any program-file write.
            originals,_=self.units();current=core.backup_records(session.call(session.camera.getBackupPresetData,True))
            if any(current[1][k].data!=v for k,v in originals.items()) or any(current[0][k].data!=b'\0' for k in core.AP_KEYS):
                raise ValueError('Target body settings changed after prepare; do not overwrite')
            self.module(session,'wbi',0)
            self.save('writing_programs');event('Writing fixed windows; do not unplug the cable or power off.')
            self.module(session,'installer',1)
            self.save('programs_written');self.files(session,True)
            self.save('writing_settings');self.settings(session)
            self.save('settings_verified');event('Programs and saved settings verified; handling the old boot snapshot.')
            self.module(session,'wbi',1)
        self.save('installed_pending_cold_start')
        event('Install and readback complete. Unplug the cable, shut down normally, wait for the access light to go out, remove the battery for 10 seconds, then reinsert it and power on.')
        event('Reset FL2/FL3 separately, take new photos and play them back; this is an experimental preview.')
    def verify(self):
        from transport import Session
        self.load()
        with Session(self.state['identity']) as session:
            # Later LUT installs legitimately change these program files.
            # Verify FL23's current patches/parameters and loaded spans.
            programs={name:session.read('/tmp/jiritsu/../..'+path) for name,path in
                [(core.PROGRAMS[0],'/usr/lib/appFw.so'),(core.PROGRAMS[1],'/cp/cpapp-b.bin')]}
            import compat
            _,enabled,_,_,_=compat.plan(programs[core.PROGRAMS[0]],programs[core.PROGRAMS[1]],
                self.state.get('version',core.VERSION),transitions=False)
            if not enabled:raise ValueError('The current programs do not fully enable FL2/FL3')
            current=core.backup_records(session.call(session.camera.getBackupPresetData,True))
            if self.state.get('compatibility',{}).get('already_enabled'):
                new={k:(self.root/'original'/f'unit-{k:08x}.bin').read_bytes() for k in core.CP_KEYS}
            else:_,new=self.units()
            if any(current[1][k].data!=v for k,v in new.items()):raise ValueError('CP parameters do not match after restart')
            if any(current[0][k].data!=bytes([10+i]) for i,k in enumerate(core.AP_KEYS)):raise ValueError('AP bindings do not match after restart')
            runtime=self.module(session,'runtime')
            candidate=programs[core.PROGRAMS[0]]
            for span in runtime['spans']:
                expected=candidate[span['offset']:span['offset']+span['length']].hex()
                if span['memory']!=expected or span['disk']!=expected:
                    raise ValueError('Runtime still holds old data; make sure the camera was shut down and the battery removed before powering on')
        self.audit('post_restart_files_and_targets_verified')
        event('On-disk programs and saved parameters match expectations; menus, photos and playback still need checking on the camera.')

def main():
    p=argparse.ArgumentParser(description='A7C II 2.01 FL2/FL3 experimental preview')
    p.add_argument('command',choices=['prepare','install','verify','check-package'])
    p.add_argument('--workspace',type=Path);p.add_argument('--backup-copy',type=Path)
    p.add_argument('--firmware-version',help='prepare: firmware version from the camera version screen, e.g. 2.01')
    p.add_argument('--battery-percent',type=int,default=-1)
    args=p.parse_args()
    if args.command=='check-package':core.assets();event('Package assets complete; this check does not connect to the camera.');return
    if not args.workspace:p.error('A body workspace folder is required')
    job=Job(args.workspace)
    try:
        if args.command=='prepare':
            if not args.backup_copy:p.error('prepare requires a second backup folder')
            if not args.firmware_version:p.error('Use --firmware-version 2.01 to enter the version shown on the camera version page')
            job.prepare(args.backup_copy,args.firmware_version)
        elif args.command=='install':job.install(args.battery_percent)
        elif args.command=='verify':job.verify()
    except Exception as exc:
        if hasattr(job,'state'):
            job.state['last_error']=str(exc);job.state['failed_during']=job.state['phase']
            job.save('needs_review')
        event('Stopped: '+str(exc));event('Do not blindly re-run writes or restart; keep the workspace for review.')
        import traceback
        diagnostic=job.root/'evidence';diagnostic.mkdir(parents=True,exist_ok=True)
        (diagnostic/f'{datetime.now():%Y%m%d-%H%M%S-%f}-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise SystemExit(1)
if __name__=='__main__':main()
