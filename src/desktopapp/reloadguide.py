"""User-visible cold reload steps, shared by the log and completion dialog."""

STEPS = (
    'Only do this after the software clearly shows "all reads and writes have finished".\n\n'
    '1. Unplug the camera\'s USB cable and disconnect any other external power.\n'
    '2. Wait for the camera\'s access lamp to stop blinking; never remove the battery while it blinks.\n'
    '3. Switch the camera power to OFF and wait until the screen and access lamp are completely dark.\n'
    '4. Remove the battery so the camera has no battery, USB or other power at all, and wait at least 1 minute.\n'
    '5. Reinsert the battery and power on.'
)

WAITING_PHASES = {'WAIT_RELOAD', 'AWAITING_RELOAD', 'RESTORED_AWAITING_RELOAD',
                  'installed_pending_cold_start','WAIT_RESOURCE_RELOAD','AWAITING_RESOURCE_RELOAD'}
SOUND_PHASES = {
    'sound_on': {'written'}, 'sound_off': {'restored'},
    'sound_install': {'installed_cold_test_pending'},
    'sound_restore_sound': {'restored_cold_test_pending'},
    'sound_confirm': set(),
}


def required(action, result):
    """Use completed backend outcomes, never guess from a write button name."""
    phase = result.get('phase')
    if result.get('reload_required') is True:
        return True
    if phase in WAITING_PHASES:
        return True
    return (phase in SOUND_PHASES.get(action, set())
            and not result.get('adopted_existing_enabled'))


def sound_notice(action,result):
    """Temporary audition needs guidance while the current power stays on."""
    phase=result.get('phase')
    if action=='sound_audition' and phase=='temporary_pcm_registered_cold_reload_required_after_test':
        return dict(title='Audition ready — keep the camera on',
            status='Audition ready. Unplug USB and keep the camera on; after a test shot, reconnect and save directly.',
            text='Camera reads and writes have finished. The current sound is a temporary audition only and is not saved permanently yet.\n\n'
                 '1. Unplug USB and keep the camera on; do not power off, remove the battery or change the Audio signals setting.\n'
                 '2. Take a shot with the electronic shutter and check the sound itself, volume, pitch/speed, and that shooting and playback work.\n'
                 '3. Reconnect USB in Mass Storage mode and click "Save current custom sound". You can save directly without restoring the original sound first.\n'
                 '4. After the save has been written, power-cycle completely as the dialog describes and check that it took effect permanently.\n\n'
                 '"Confirm audition is correct" only records the audition result and is optional.\n'
                 'OK in this dialog only closes the instructions; it does not confirm the audition.')
    if action=='sound_confirm' and phase in ('owner_confirmed_audio_cold_reload_required',
            'owner_audio_failed_cold_reload_required','owner_requested_gain_adjustment_cold_reload_required'):
        return dict(title='Audition result recorded',status='Audition record saved; you can save the current custom sound directly without power-cycling first.',
                    text='This step only records the audition result.\n\nYou can click "Save current custom sound" directly, without power-cycling or recording a restore first. '
                    'If you are not satisfied, adjust the clip and convert again; to clear the temporary audition, follow the power-cycle steps to restore the original sound.')
    if action!='sound_install':return None
    if phase=='sound_conversion_required':
        return dict(title='Save not started — convert a clip first',status='Waiting: choose a sound file; once converted it can be saved directly.',
                    text='There is no converted clip to save; nothing was written to the camera.\n\nChoose an audio or video file, set the start and length, '
                    'then click "Convert selected clip"; after a successful conversion click "Save current custom sound". The audition is optional.')
    return None


def text(*, setup=False, mode=None):
    if mode=='factory_prewrite_temporary':
        return ('This restore has not started writing yet, and the connection has ended. The camera holds a temporary work file with the same name, '
                'and the file name alone cannot tell which operation left it; it was not overwritten and the restore was not marked complete.\n\n'
                'First power-cycle completely so the temporary service state exits, then the current camera will be read again and a new restore plan generated.\n\n'+STEPS+
                '\n\nNext: reconnect USB in Mass Storage mode and click "Retry restore after power cycle (nothing written yet)" on the restore page. '
                'The tool rereads the current program, settings and names and restores factory functions from the current state; no old LUT task is needed. '
                'If a temporary file conflict is still reported, export a new diagnostic package; do not delete camera files by hand.'
                '\n\nThis is a retry step before any restore write, not "restore complete" or "verify after restart".')
    if mode=='factory_reset':
        return ('Restore not finished yet: writing and full readback have ended, but the camera\'s actual loaded state must still be verified after a restart.\n\n'+STEPS+
                '\n\nNext: confirm the camera shows a normal live view, reconnect USB in Mass Storage mode, and click '
                '"Verify after restart and finish restore" at the top of the restore page, or "Verify after restart and finish restore (required after a restore write)" below.\n\n'
                'Restore is shown as complete only after verification passes. If verification fails, keep the log; do not treat the end of writing as a completed restore. '
                'OK in the dialog only closes the instructions; it does not complete verification.')
    if mode=='resource_reload':
        return ('The name stage is complete; the program has not been written yet. The camera still holds the old resources and the read-only mount has not been restored; the old resources must be released before the rest of the installation continues.\n\n'+STEPS+
            '\n\nNo need to take photos after powering on. Reconnect USB in Mass Storage mode, then click '+('"Continue installation" on the Home page' if setup else '"Continue slot changes" on the Custom Creative Looks page')+
            '. The tool verifies the new cold boot and read-only mount, then continues with the remaining program, without rewriting names or reinstalling drivers.\n\nAfter the program is written you will be asked for a final restart so the new functions take effect. OK only closes the instructions.')
    reason = ('\n\n"Enable FL2/FL3" has now been written to the program file. The restart after the earlier factory restore only loaded the factory state; this new change needs another restart to take effect.'
              if mode == 'fl23_enable' else '')
    follow = ('Reconnect USB, select Mass Storage, then click "Continue installation" on the Home page. The tool verifies loading first and does not flash again.'
              if setup else 'On the camera, confirm that FL2/FL3 can be selected, shot and played back, and it is ready to use. No need to reconnect the computer to verify; for troubleshooting, use the optional diagnostic on the FL2 / FL3 page.'
              if mode in ('fl23_enable', 'fl23_disable') else
              'This power cycle only clears the temporary audition and restores the original sound; it is not a prerequisite for saving a sound. After powering on, confirm the original sound, shooting and playback are normal, then you can click "Power-cycled to restore original sound; record restore complete" on the sound page. Saving the current converted clip does not require this step.'
              if mode == 'sound_confirm' else
              'After powering on, shoot with the electronic shutter and check the sound, volume and shooting/playback. After saving a custom sound, you can verify its loaded state on the sound page.'
              if mode and mode.startswith('sound_') else
              'The vertical display switch and frame references have been saved. After restarting, first hold the camera horizontally and check the Fn grid and moving the selection right, then hold it vertically to each side and check the frames of Fn, Creative Look and other submenus; finally check shooting and playback. Known issues: in vertical orientation the outer frame of the Creative Look selection page is still too thick; the scale is now shown horizontally, but the orange pointer direction is not fixed yet.'
              if mode == 'vertical_enable' else
              'Vertical display was turned off first, the original frame references and resource index were restored, and helper aliases were removed. If the running firmware still references appended images, a small amount of image tail data is kept for now to avoid breaking the current display; this does not affect turning it off and needs no further clicks. After restarting, confirm horizontal/vertical display and shooting are normal.'
              if mode == 'vertical_disable' else
              'Switch between ST and the changed slots in random order and confirm the live preview updates immediately, then take photos and play them back. A look-only write needs no separate verification from the computer; if the name stage reports that the program is not written yet, reconnect and click "Continue slot changes".'
              if mode in ('install_all','look_import','slot_default') else
              'Confirm a normal live view, check the menu/look preview, and take photos and play them back. If this page shows a pending verification, reconnect USB and click the verify button listed on that page.')
    check_note='The load verification only reads state; it does not flash again. ' if setup or (mode and mode.startswith('sound_')) else ''
    return STEPS + reason + '\n\nNext: ' + follow + '\n\n' + check_note + 'Clicking OK only closes the instructions; it does not power off the camera or confirm the tests for you.'
