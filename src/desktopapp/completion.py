"""Human-readable completed setup; detailed evidence stays in private files."""


def archive_error(state):
    error=state.pop('error',None)
    if error:
        state.setdefault('previous_errors',[]).append(dict(phase=state.get('phase'),error=error))
        return True
    return False


def text(state):
    if state.get('phase')!='COMPLETE':raise ValueError('The previous installation has not finished; use "Continue installation".')
    options=state.get('options',{})
    lines=['The selected operations are complete; program and settings checks passed.','Check preview, shooting and playback on the camera.','',
        'FL2/FL3: '+('enabled' if options.get('fl23',True) else 'not changed this time')]
    looks=options.get('looks',[])
    if looks:
        lines.append('Custom looks: written')
        lines.extend('  Custom %s: %s'%(row['slot'],row.get('name') or 'name from file') for row in looks)
    else:lines.append('Custom looks: not changed this time')
    lines.append('Electronic shutter sound: '+('support enabled; check the camera\'s Audio signals setting' if options.get('sound',True) else 'not selected this time'))
    if options.get('plugin'):lines.append('Lightroom plug-in: installed; enable it in the Plug-in Manager')
    if options.get('vertical',True):
        if state.get('vertical_result',{}).get('persistent') and state['vertical_result'].get('loaded_verified'):
            lines.append('Vertical shooting info: saved as on, and the running state after restart was verified; no need to turn it on from the computer each time.')
        else:
            lines.extend(['Vertical shooting info: the old version only turned it on for this session.',
                'The old task did not save it as the power-on default; save it as on from the new "Vertical Display" page.'])
    else:lines.append('Vertical shooting info: not changed this time')
    lines.extend(['','This installation has finished; there is no need to flash again just to view the result.'])
    return '\n'.join(lines)


def console_summary(state):
    return {key:state[key] for key in ('schema','phase','workspace','message') if key in state} | {
        'looks':[dict(slot=r['slot'],name=r.get('name')) for r in state.get('options',{}).get('looks',[])],
        'completed_steps':state.get('completed_steps',[]),
        'physical_checks_accepted':state.get('physical_checks_accepted',False),
        'previous_error_count':len(state.get('previous_errors',[]))}
