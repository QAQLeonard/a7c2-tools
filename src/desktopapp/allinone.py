"""Guided combined persistent install, cold reload and loaded-state verification.

All device work goes through existing explicit worker actions. A failed or
unknown installation is never replayed. Physical power removal remains manual.
"""
import json
import uuid
from pathlib import Path
from .paths import data_root, write_json
from . import lookbatch


def run(arguments, *, dispatch):
    from looktool import bundle, settingsresume
    from looktool.power import require_power
    require_power(confirmed=arguments.get('power_confirmed', False))
    if arguments.get('firmware') != '2.01':
        raise ValueError('One-click setup supports ILCE-7CM2 2.01')
    root = Path(arguments['workspace']).resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = root / 'setup.private.json'
    state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
    if state and state['phase'] == 'COMPLETE':
        from .completion import archive_error
        if archive_error(state):write_json(path,state)
        print('This one-click install has already finished; nothing was written again.', flush=True)
        return state
    if state is None:
        from .presets import resolve
        inputs = root / 'inputs'
        inputs.mkdir(exist_ok=True)
        options, _ = bundle.documents(resolve(arguments.get('options', {})), inputs)
        # Version the behavior so already-written older jobs keep their plan.
        options['vertical_persistent'] = bool(options.get('vertical', True))
        options['portrait_frames'] = bool(options.get('vertical', True))
        if options.get('plugin'):
            from .exiftool import ensure
            options['exiftool']=ensure(options.get('exiftool'))
        state = dict(schema='a7c2-one-click/1', phase='READY', workspace=str(root), options=options,
                     firmware='2.01', completed_steps=[], physical_checks_accepted=False)
        write_json(path, state)

    def save(phase, **values):
        if phase!='NEEDS_REVIEW' and 'error' not in values:
            from .completion import archive_error
            archive_error(state)
        state.update(values, phase=phase)
        write_json(path, state)
        print('One-click install: ' + phase, flush=True)

    def call(action, values, name):
        step = root / 'steps' / name
        step.mkdir(parents=True, exist_ok=True)
        print('Running: ' + action, flush=True)
        return dispatch(action, values, step)

    options = state['options']
    common = dict(firmware='2.01', power_confirmed=True)
    install = Path(state.get('install_workspace') or root / 'install')
    if state['phase']=='NEEDS_REVIEW' and state.get('verify_result',{}).get('phase') in ('LOADED','COMPLETE'):
        # Older packages called a computer-only plugin failure NEEDS_REVIEW.
        # Once camera work was verified, resume only the remaining host steps.
        done=state.get('completed_steps',[])
        child=install/'direct.private.json'
        verified=state['verify_result'].get('workspace')
        if ('persistent_features' in done and (not options.get('sound',True) or 'sound' in done)
                and (not options.get('vertical',True) or options.get('vertical_persistent'))
                and verified and Path(verified).resolve()==install.resolve() and child.is_file()
                and json.loads(child.read_text(encoding='utf-8')).get('phase') in ('LOADED','COMPLETE')):
            print('Camera installation and post-restart verification passed; only the computer-side plug-in step continues.',flush=True)
            save('FINALIZING')
    if state['phase']=='PREPARING_VERTICAL' or (state['phase']=='NEEDS_REVIEW' and state.get('failed_step')=='portrait_frames'):
        print('Rereading the current vertical display and frame state to resume this installation; identical content is not written again.',flush=True)
        save('PREPARED')
    if state['phase'] in ('INSTALLING', 'NEEDS_REVIEW', 'RESUMING_RESOURCES','RESUMING_SETTINGS'):
        child = install / 'direct.private.json'
        child_state = json.loads(child.read_text(encoding='utf-8')) if child.exists() else {}
        # A ready resource checkpoint can start its program child before the
        # parent receives the returned workspace. Recover that exact child.
        nested=install/'program-install/direct.private.json'
        if child_state.get('phase')=='RESOURCE_RELOAD_VERIFIED' and nested.is_file():
            install=nested.parent
            child_state=json.loads(nested.read_text(encoding='utf-8'))
            state['install_workspace']=str(install)
        if (state['phase'] in ('RESUMING_SETTINGS','NEEDS_REVIEW') and state.get('resume_settings_from') and not child_state and
                (not install.exists() or not any(install.iterdir()))):
            install=Path(state['resume_settings_from'])
            save('SETTINGS_REVIEW_REQUIRED',install_workspace=str(install))
        elif (state['phase']=='RESUMING_RESOURCES' and not child_state and
                (not install.exists() or not any(install.iterdir()))):
            # Dispatch never created a transaction; continue from the saved
            # resource source in a fresh child, never reuse an unknown job.
            install=Path(state['resume_resource_from'])
            save('WAIT_RESOURCE_RELOAD',install_workspace=str(install))
        elif child_state.get('phase') in ('AWAITING_RESOURCE_RELOAD','RESOURCE_RELOAD_VERIFIED'):
            save('WAIT_RESOURCE_RELOAD')
        elif child_state.get('phase') in ('AWAITING_RELOAD', 'LOADED', 'COMPLETE'):
            # Re-read device proof even when the child finished before the
            # parent saved its result. LOADED children need no further reboot.
            save('WAIT_RELOAD')
        elif (child_state.get('schema')=='a7c2-direct-job/1' and child_state.get('mode')=='install_all'
              and not child_state.get('settings_resume_from')
              and isinstance(child_state.get('journal'),list)
              and lookbatch.read_only_failure(child_state)):
            # A version/window conflict can occur while building the host plan,
            # before any camera write. A fixed tool must allow a fresh plan,
            # preserving the failed child and its saved selection.
            print('The previous installation stopped before writing; keeping the failure record and generating a new plan with the current code, without reinstalling drivers.',flush=True)
            state.setdefault('failed_install_workspaces',[]).append(str(install))
            install=root/('install-retry-'+uuid.uuid4().hex[:8])
            save('PREPARED',install_workspace=str(install))
        elif settingsresume.eligible(child_state):
            save('SETTINGS_REVIEW_REQUIRED')
        else:
            from . import reviewnames
            try:reviewnames.source(install)
            except (ValueError,OSError,KeyError):
                from looktool import namespause
                try:namespause.source(install)
                except (ValueError,OSError,KeyError):
                    detail='; original stage: %s; original error: %s'%(child_state.get('failed_during',child_state.get('phase','unknown')),
                        child_state.get('error','original error missing; export a new diagnostic package that includes the child transaction'))
                    raise ValueError('The previous installation result needs review and will not be flashed again. Keep this folder and check the full error: ' + str(root)+detail)
                save('RESOURCE_REVIEW_REQUIRED')
            else:
                print('Last time there was not enough space before the names were committed; verifying existing bytes first and cleaning up that run\'s finished temporary reports.',flush=True)
                reviewed=call('review_failed_names',dict(workspace=str(install)),'review-'+uuid.uuid4().hex[:6])
                if not reviewed.get('pre_program_failure_accounted'):raise ValueError('Name failure review did not finish; no retry')
                state.setdefault('failed_install_workspaces',[]).append(str(install))
                install=root/('install-retry-'+uuid.uuid4().hex[:8])
                save('PREPARED',install_workspace=str(install),last_name_failure_review=reviewed)
    host_step=False
    try:
        if state['phase']=='SETTINGS_REVIEW_REQUIRED':
            previous=install
            failed=state.setdefault('failed_install_workspaces',[])
            if str(previous) not in failed:failed.append(str(previous))
            candidate=root/('install-settings-'+uuid.uuid4().hex[:8])
            save('RESUMING_SETTINGS',resume_settings_from=str(previous),install_workspace=str(candidate))
            print('The program and names were fully read back last time; after verifying the current contents only the settings continue, without reinstalling drivers or flashing the program again.',flush=True)
            result=call('direct_resume_settings',dict(common,workspace=str(candidate),failed_workspace=str(previous)),
                        'settings-resume-'+uuid.uuid4().hex[:6])
            install=Path(result['workspace']);state['install_result']=result
            if result['phase']!='AWAITING_RELOAD':raise ValueError('Settings continuation did not reach reload preparation')
            save('WAIT_RELOAD')
            from .reloadguide import text
            print('All reads and writes have finished.\n'+text(setup=True),flush=True)
            return state
        if state['phase'] in ('WAIT_RESOURCE_RELOAD','RESOURCE_REVIEW_REQUIRED'):
            print('Names are already written; verifying/preparing the resource reload, without rewriting names or reinstalling drivers.',flush=True)
            previous=install
            candidate=root/('install-continue-'+uuid.uuid4().hex[:8])
            save('RESUMING_RESOURCES',resume_resource_from=str(previous),install_workspace=str(candidate))
            result=call('direct_resume_looks',dict(common,workspace=str(candidate),failed_workspace=str(previous)),
                        'resource-resume-'+uuid.uuid4().hex[:6])
            if result['phase']=='RESOURCE_RELOAD_VERIFIED':
                previous=Path(result['workspace'])
                candidate=root/('install-after-resources-'+uuid.uuid4().hex[:8])
                save('RESUMING_RESOURCES',resume_resource_from=str(previous),install_workspace=str(candidate))
                result=call('direct_resume_looks',dict(common,workspace=str(candidate),failed_workspace=str(previous)),
                            'resource-continue-'+uuid.uuid4().hex[:6])
            install=Path(result['workspace']);state['install_workspace']=str(install)
            if result['phase']=='AWAITING_RESOURCE_RELOAD':
                # A names-only preparation returns a checkpoint; never treat
                # it as a completed program install or enable other features.
                save('WAIT_RESOURCE_RELOAD',resource_result=result)
                from .reloadguide import text
                print('All reads and writes have finished.\n'+text(setup=True,mode='resource_reload'),flush=True)
                return state
            state['install_result']=result
            state['completed_steps'].append('persistent_features')
            if result['phase']=='AWAITING_RELOAD':
                save('WAIT_RELOAD');return state
            save('FINALIZING')
        if state['phase'] == 'READY':
            save('DRIVERS')
            result = call('usb_prepare', {}, 'drivers')
            state['driver_result'] = result
            state['completed_steps'].append('drivers')
            save('PREPARED')
        if state['phase'] == 'DRIVERS':
            print('Last time stopped at connection preparation; this time only the connection is tested, without changing drivers again.', flush=True)
            state['driver_result'] = call('connect', {}, 'driver-recheck')
            state['completed_steps'].append('drivers')
            save('PREPARED')
        if state['phase'] == 'PREPARED':
            if options.get('portrait_frames') and not state.get('portrait_frames_preinstalled'):
                save('PREPARING_VERTICAL',failed_step='portrait_frames')
                result=call('vertical_enable',dict(common,workspace=str(root/'vertical'),drivers_prepared=True,combined=True),
                            'vertical-frames-'+uuid.uuid4().hex[:6])
                if result.get('phase') not in ('AWAITING_RELOAD','LOADED','COMPLETE'):
                    raise ValueError('The vertical frame step did not report a written / already-at-target state; please keep the log')
                state['portrait_frames_preinstalled']=True
                state['portrait_frames_result']=result
                state.pop('failed_step',None)
                save('PREPARED')
            save('INSTALLING')
            result = call('direct_install_all', dict(common, workspace=str(install), options=options), 'install')
            state['install_result'] = result
            if result['phase']=='AWAITING_RESOURCE_RELOAD':
                save('WAIT_RESOURCE_RELOAD')
                from .reloadguide import text
                print('All reads and writes have finished.\n'+text(setup=True,mode='resource_reload'),flush=True)
                return state
            state['completed_steps'].append('persistent_features')
            if result['phase'] == 'AWAITING_RELOAD':
                save('WAIT_RELOAD')
                from .reloadguide import text
                print('Program/look writing and full readback for this run have finished.\n' + text(setup=True), flush=True)
                return state
            save('FINALIZING')
        if state['phase'] == 'WAIT_RELOAD':
            print('Continuing the saved installation plan; verifying the new power-on first, without flashing again.', flush=True)
            try:
                result = call('direct_verify', dict(workspace=str(install), accepted=False), 'verify')
            except ValueError as exc:
                # Match both the original and the translated backend message.
                if '冷启动' in str(exc) or 'cold boot' in str(exc).lower():
                    save('WAIT_RELOAD', message=str(exc))
                    print(str(exc), flush=True)
                    return state
                raise
            state['verify_result'] = result
            if 'persistent_features' not in state['completed_steps']:
                state['completed_steps'].append('persistent_features')
            save('FINALIZING')
        if state['phase'] == 'FINALIZING':
            if options.get('sound',True) and 'sound' not in state['completed_steps']:
                sound=root/'sound'
                state['sound_result']=call('sound_on',dict(common,workspace=str(sound),backup=str(root/'sound-backups')),'sound-adoption')
                state['sound_workspace']=str(sound)
                state['sound_backup']=str(root/'sound-backups')
                state['completed_steps'].append('sound')
                save('FINALIZING')
            if options.get('plugin') and 'plugin' not in state['completed_steps']:
                host_step=True
                state['plugin_result'] = call('plugin_install', {'exiftool': options.get('exiftool')}, 'plugin')
                child = json.loads((install / 'direct.private.json').read_text(encoding='utf-8'))
                _, rows = bundle.documents(child['bundle_options'])
                if rows:
                    from looktool.rawidentity import activated
                    state['raw_profile_result'] = activated(
                        [dict(r['document'], name=r['name']) for r in rows], [r['slot'] for r in rows],
                        child['job_id'], child['raw_profile_effective_since'])
                state['completed_steps'].append('plugin')
                save('FINALIZING')
                host_step=False
            if options.get('vertical', True) and 'vertical' not in state['completed_steps']:
                if options.get('vertical_persistent'):
                    result = state.get('verify_result', state.get('install_result', {})).get('vertical_result', {})
                    if not (result.get('persistent') and result.get('loaded_verified') and
                            result.get('saved') == result.get('running') == 'ON' and result.get('alias_count') == 3):
                        raise ValueError('Persistent loading of vertical display is not confirmed yet; a temporary session-only enable does not count as complete. Please keep the log.')
                    state['vertical_result'] = result
                else:
                    # Resume old plans without silently adding a new flash write.
                    state['vertical_result'] = call('vertical_enable', dict(common, workspace=str(root / 'vertical'), session_only=True), 'vertical')
                state['completed_steps'].append('vertical')
            message='The selected installation is complete; check preview, names, shooting and playback on the camera. '
            if options.get('vertical',True):
                message+=('Vertical display is saved as on, and the actual running state after restart was verified.' if options.get('vertical_persistent') else
                    'With the old installation, vertical display was only on for this power-on; save it as on from the new Vertical Display page.')
            save('COMPLETE', message=message)
            print(state['message'], flush=True)
        return state
    except BaseException as exc:
        if state['phase']=='FINALIZING' and host_step:
            save('FINALIZING',error=str(exc))
        elif state['phase'] not in ('DRIVERS', 'WAIT_RELOAD'):
            save('NEEDS_REVIEW', error=str(exc))
        else:
            save(state['phase'], error=str(exc))
        raise
