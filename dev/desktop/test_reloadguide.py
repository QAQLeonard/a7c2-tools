"""Every completed cold-reload path gets guidance; temporary features stay on."""
import unittest
from desktopapp import reloadguide


class ReloadGuideTests(unittest.TestCase):
    def test_all_completed_cold_reload_paths(self):
        cases = [('setup_all','WAIT_RELOAD'), ('direct_fl23_enable','AWAITING_RELOAD'),
            ('direct_fl23_disable','AWAITING_RELOAD'), ('direct_look_import','AWAITING_RELOAD'),
            ('direct_slot_default','AWAITING_RELOAD'), ('direct_factory_reset','AWAITING_RELOAD'),
            ('direct_resume_factory','AWAITING_RELOAD'), ('restore','RESTORED_AWAITING_RELOAD'),
            ('restore_auto','RESTORED_AWAITING_RELOAD'), ('look_install','AWAITING_RELOAD'),
            ('look_restore','RESTORED_AWAITING_RELOAD'), ('fl23_install','installed_pending_cold_start'),
            ('sound_on','written'), ('sound_off','restored'), ('sound_install','installed_cold_test_pending'),
            ('sound_restore_sound','restored_cold_test_pending')]
        cases += [('sound_confirm', phase) for phase in reloadguide.SOUND_PHASES['sound_confirm']]
        for action, phase in cases:
            with self.subTest(action=action, phase=phase):
                self.assertTrue(reloadguide.required(action, dict(phase=phase)))

    def test_no_cold_restart_before_audition_or_for_adoption_offline_and_failures(self):
        cases = [('sound_audition','temporary_pcm_registered_cold_reload_required_after_test'),
            ('sound_confirm_recovery','owner_confirmed_cold_recovered'), ('sound_import','converted_offline'),
            ('sound_verify','owner_confirmed_working'), ('vertical_enable','running'),
            ('direct_verify','LOADED'), ('direct_fl23_enable','LOADED'),
            ('direct_fl23_enable','PREFLIGHT_VERIFIED'), ('direct_fl23_enable','NEEDS_REVIEW'),
            ('sound_install','needs_review')]
        for action, phase in cases:
            with self.subTest(action=action):self.assertFalse(reloadguide.required(action, dict(phase=phase)))
        self.assertFalse(reloadguide.required('sound_on', dict(phase='written', adopted_existing_enabled=True)))

    def test_sound_confirmation_instructions_preserve_the_audition_sequence(self):
        text = reloadguide.text(mode='sound_confirm')
        self.assertIn('clears the temporary audition and restores the original sound', text)
        self.assertIn('Power-cycled to restore original sound; record restore complete', text)
        self.assertIn('wait at least 1 minute', text)

    def test_audition_popup_keeps_power_until_listening_not_cold_reload(self):
        result=dict(phase='temporary_pcm_registered_cold_reload_required_after_test')
        self.assertFalse(reloadguide.required('sound_audition',result))
        notice=reloadguide.sound_notice('sound_audition',result)
        for phrase in ('keep the camera on','do not power off','electronic shutter','Confirm audition is correct','without restoring the original sound first','Save current custom sound'):
            self.assertIn(phrase,notice['text'])
        self.assertIn('only closes the instructions',notice['text'])

    def test_install_prerequisites_have_distinct_guidance_not_failure_or_fake_completion(self):
        for phase in ('sound_conversion_required',):
            notice=reloadguide.sound_notice('sound_install',dict(phase=phase))
            self.assertIn('Save not started',notice['title'])
            self.assertIn('Waiting',notice['status'])
        notice=reloadguide.sound_notice('sound_confirm',dict(phase='owner_confirmed_audio_cold_reload_required'))
        self.assertIn('without power-cycling or recording a restore first',notice['text'])
        for phase in ('needs_review','installed_cold_test_pending'):
            self.assertIsNone(reloadguide.sound_notice('sound_install',dict(phase=phase)))


def test_setup_reload_names_continue_button():
    for mode in (None,'resource_reload'):
        message=reloadguide.text(setup=True,mode=mode)
        assert 'Continue installation' in message
        assert 'Continue previous installation' not in message
        assert 'reconnect usb' in message.lower()
