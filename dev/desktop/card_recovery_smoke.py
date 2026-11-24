def run():
    from unittest.mock import patch
    from PySide6 import QtWidgets as W
    from desktopapp import VERSION,window,worker,jobs,usbrecovery
    assert usbrecovery.TARGET==b'\0\x02'
    app=W.QApplication.instance() or W.QApplication([])
    view=window.Window(demo=True)
    try:
        view.timer.stop()
        assert VERSION=='3.11' and view.recovery_transport.value()=='usb'
        assert '2.00' in view.factory_button.text()
        with patch.object(view,'launch') as launch:view.factory_button.click()
        action,args=launch.call_args.args
        assert action=='usb_restore_version' and action in jobs.POWER_ACTIONS
        view.recovery_transport.select('ssh')
        with patch.object(view,'launch') as launch:
            view.findChild(W.QPushButton,'action_ssh_restore_version').click()
        assert launch.call_args.args[0]=='ssh_restore_version'
        with patch.object(view,'launch') as launch:
            view.findChild(W.QPushButton,'action_firmware_factory_build').click()
        assert launch.call_args.args[0]=='firmware_factory_build'
        assert not hasattr(view,'factory_voice')
        try:worker.run('direct_factory_reset',{},None)
        except ValueError as exc:assert '旧 USB' in str(exc)
        else:raise AssertionError('Old recovery was not blocked')
        return dict(version=VERSION,USB_version_only=True,SSH_version_only=True,
            both_transports_offer_card_package=True,legacy_factory_recovery_blocked=True,
            frozen_UI_dispatch_passed=True,camera_io=False)
    finally:view.close()
