"""Six explicit workflows, background workers and a complete diagnostic log."""
from datetime import datetime
import json
from pathlib import Path
import sys
import uuid
from PySide6 import QtCore, QtGui, QtWidgets as W
from . import VERSION
from . import jobs
from . import presets
from . import reloadguide

DRIVER_HINT = ('\nDriver or connection did not succeed: first uninstall and reinstall the drivers on the "Connection & Drivers" page; if that still fails, '
               'click "Install driver manually with Zadig" on that page and follow the steps to install libusbK for both identities, 0E8A and 0336.')
from . import connectionguide
from .paths import ROOT, data_root, load_settings, write_json
from .theme import WINDOW as STYLE


class Window(W.QMainWindow):
    def __init__(self, *, demo=False):
        super().__init__()
        self.setWindowTitle('A7C II Tools · Desktop Preview')
        self.resize(1130, 850)
        self.setMinimumSize(960, 730)
        self.settings = load_settings()
        self.fields, self.buttons = {}, []
        self.current_job = None
        self.log_offset = 0
        self.process = None
        self.demo = demo
        self.camera_operation = False
        self.setStyleSheet(STYLE)
        central = W.QWidget()
        self.setCentralWidget(central)
        layout = W.QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        self.nav = W.QListWidget()
        self.nav.setFixedWidth(235)
        self.nav.addItems(['Home · One-click install', 'Connection & Drivers', 'Factory Restore', 'FL2 / FL3', 'Custom Creative Looks', 'Vertical Display', 'Electronic Shutter Sound'])
        layout.addWidget(self.nav)
        right = W.QVBoxLayout()
        right.setContentsMargins(22, 18, 22, 16)
        layout.addLayout(right, 1)
        heading = W.QHBoxLayout()
        title = W.QLabel('A7C II Tools')
        title.setStyleSheet('font-size:25px;font-weight:650;')
        heading.addWidget(title)
        heading.addStretch()
        heading.addWidget(W.QLabel('Firmware version'))
        self.firmware = W.QComboBox()
        self.firmware.addItems(['2.01'])
        heading.addWidget(self.firmware)
        right.addLayout(heading)
        self.description = W.QLabel(('Windows test build' if sys.platform == 'win32' else 'Desktop development build') + ' · One-click install and six feature pages · ' + VERSION)
        self.description.setProperty('hint', True)
        right.addWidget(self.description)
        self.pages = W.QStackedWidget()
        right.addWidget(self.pages, 1)
        self.home_page()
        self.connection_page()
        self.recovery_page()
        self.fl23_page()
        self.look_page()
        self.vertical_page()
        self.sound_page()
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)
        self.progress = W.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        right.addWidget(self.progress)
        self.status = W.QLabel('Ready. Choose a feature on the left; starting the software does not access the camera.')
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(180)
        self.log.setPlaceholderText('The full run log and raw error messages appear here.')
        right.addWidget(self.log)
        bottom = W.QHBoxLayout()
        open_log = W.QPushButton('Open task folder')
        open_log.clicked.connect(self.open_job)
        bottom.addWidget(open_log)
        export = W.QPushButton('Export diagnostics')
        export.clicked.connect(self.export_logs)
        bottom.addWidget(export)
        bottom.addStretch()
        self.stop = W.QPushButton('Stop offline task')
        self.stop.setEnabled(False)
        self.stop.clicked.connect(self.cancel_offline)
        bottom.addWidget(self.stop)
        right.addLayout(bottom)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.poll_job)
        self.timer.start(250)

    def page(self, title, detail):
        wrapper = W.QScrollArea()
        wrapper.setWidgetResizable(True)
        body = W.QWidget()
        layout = W.QVBoxLayout(body)
        layout.setContentsMargins(0, 8, 8, 8)
        label = W.QLabel(title)
        label.setStyleSheet('font-size:20px;font-weight:600;')
        layout.addWidget(label)
        hint = W.QLabel(detail)
        hint.setWordWrap(True)
        hint.setProperty('hint', True)
        layout.addWidget(hint)
        wrapper.setWidget(body)
        self.pages.addWidget(wrapper)
        return layout

    def box(self, layout, title):
        group = W.QGroupBox(title)
        form = W.QFormLayout(group)
        form.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow)
        layout.addWidget(group)
        return form

    def advanced(self, layout, title):
        toggle = W.QToolButton()
        toggle.setText(title)
        toggle.setCheckable(True)
        toggle.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        toggle.setArrowType(QtCore.Qt.RightArrow)
        content = W.QWidget()
        content.setVisible(False)
        inner = W.QVBoxLayout(content)
        inner.setContentsMargins(0, 0, 0, 0)
        toggle.toggled.connect(content.setVisible)
        toggle.toggled.connect(lambda open: toggle.setArrowType(QtCore.Qt.DownArrow if open else QtCore.Qt.RightArrow))
        layout.addWidget(toggle)
        layout.addWidget(content)
        return inner

    def direct_args(self, group, **values):
        work = self.work(group)
        return dict(self.common(), workspace=work, **{key: value for key, value in values.items() if key != 'mode'})

    def setup_args(self):
        root = self.settings.get('setup_work', '')
        state = Path(root, 'setup.private.json') if root else None
        if state is not None and state.is_file():
            saved = json.loads(state.read_text(encoding='utf-8'))
            if saved['phase'] != 'COMPLETE':
                return dict(self.common(), workspace=root, options=saved['options'])
        root = self.work('setup')
        tool = ROOT / ('desktop-assets/exiftool/exiftool.exe' if sys.platform=='win32' else 'desktop-assets/exiftool/exiftool')
        looks = [dict(slot=s, path=self.text('setup_look_' + str(s))) for s in range(1, 7) if self.text('setup_look_' + str(s))]
        options = dict(fl23=self.setup_fl23.isChecked(), sound=self.setup_sound.isChecked(),
            vertical=self.setup_vertical.isChecked(), plugin=self.setup_plugin.isChecked(),
            exiftool=str(tool), looks=[] if self.setup_presets.isChecked() else looks,
            preset_pack=presets.PACK if self.setup_presets.isChecked() else None)
        return dict(self.common(), workspace=root, options=options)

    def home_page(self):
        layout = self.page('One-click install', 'Installs the six looks, FL2/FL3, electronic shutter sound and the saved vertical display switch together. After the prompted power cycle, the same button only verifies loading; no slot-by-slot installation needed.')
        self.setup_presets = W.QCheckBox('Install the six built-in looks (replaces Custom 1–6; the original Creative Looks are kept)')
        self.setup_presets.setChecked(True)
        self.setup_fl23 = W.QCheckBox('Enable FL2/FL3'); self.setup_fl23.setChecked(True)
        self.setup_sound = W.QCheckBox('Enable Sony native electronic shutter sound'); self.setup_sound.setChecked(True)
        self.setup_vertical = W.QCheckBox('Save vertical shooting info display as on (takes effect automatically after restart)'); self.setup_vertical.setChecked(True)
        self.setup_plugin = W.QCheckBox('Install the Lightroom auto-detect plug-in (requires Lightroom)')
        prior_path=Path(self.settings.get('setup_work',''),'setup.private.json')
        prior=json.loads(prior_path.read_text(encoding='utf-8')) if prior_path.is_file() else {}
        if prior and prior.get('phase')!='COMPLETE':
            options=prior['options']
            self.setup_presets.setChecked(options.get('preset_pack') == presets.PACK)
            for box,key in ((self.setup_fl23,'fl23'),(self.setup_sound,'sound'),(self.setup_vertical,'vertical'),(self.setup_plugin,'plugin')):
                box.setChecked(bool(options.get(key,key!='plugin')))
            for box in (self.setup_presets,self.setup_fl23,self.setup_sound,self.setup_vertical,self.setup_plugin):box.setEnabled(False)

        self.setup_note=W.QLabel('Installation has not finished. Click "Continue installation" and follow the dialog for the next step; if a power cycle is needed, reconnect USB and click this button again.')
        self.setup_note.setWordWrap(True)
        self.setup_note.setVisible(bool(prior) and prior.get('phase')!='COMPLETE')
        layout.addWidget(self.setup_note)
        layout.addWidget(self.setup_presets)
        self.setup_preset_summary = W.QLabel(presets.SUMMARY)
        self.setup_preset_summary.setWordWrap(True)
        if prior and prior.get('phase')!='COMPLETE':
            names = ['%s %s' % (r['slot'], r.get('name', Path(r['path']).stem)) for r in prior['options'].get('looks', [])]
            self.setup_preset_summary.setText('Looks saved for this run: ' + (' · '.join(names) if names else 'no looks selected; the six looks will not be added'))
        else:
            self.setup_preset_summary.setEnabled(self.setup_presets.isChecked())
            self.setup_presets.toggled.connect(self.setup_preset_summary.setEnabled)
        layout.addWidget(self.setup_preset_summary)
        for check in (self.setup_fl23, self.setup_sound, self.setup_vertical, self.setup_plugin):layout.addWidget(check)
        self.setup_button=self.button(layout, 'Start a new one-click install' if prior.get('phase')=='COMPLETE' else 'Continue installation' if prior else 'One-click install',
                                      'setup_all', self.setup_args, primary=True)
        self.setup_result_button=W.QPushButton('View last installation result (does not connect the camera)')
        self.setup_result_button.clicked.connect(self.show_setup_result)
        self.setup_result_button.setVisible(prior.get('phase')=='COMPLETE')
        layout.addWidget(self.setup_result_button);self.buttons.append(self.setup_result_button)
        look_section=self.advanced(layout,'Use your own A7Look files instead (untick the six built-in looks first)')
        custom_container = self.setup_custom_container = look_section.parentWidget()
        custom_container.setEnabled(not self.setup_presets.isChecked() and not (prior and prior.get('phase')!='COMPLETE'))
        self.setup_presets.toggled.connect(lambda enabled: custom_container.setEnabled(not enabled))
        form = self.box(look_section, 'Choose A7Look files')
        for slot in range(1, 7):
            self.field(form, 'setup_look_' + str(slot), 'Custom ' + str(slot), kind='file', filter='Compiled looks (*.a7look)')
        compile_button = W.QPushButton('Generate A7Look from DCP/LUT…')
        compile_button.clicked.connect(self.compiler_dialog); look_section.addWidget(compile_button); self.buttons.append(compile_button)
        hint = W.QLabel('Factory restore, driver uninstall and look removal are never mixed into the installation. For a custom sound, convert and save it on the "Electronic Shutter Sound" page; the audition is optional.')
        hint.setWordWrap(True); layout.addWidget(hint); layout.addStretch()

    def drivers_first(self, arguments):
        """Suggest the connection page before a first one-click install on Windows."""
        if (sys.platform != 'win32' or self.settings.get('connection_verified')
                or Path(arguments.get('workspace', ''), 'setup.private.json').is_file()):
            return True
        choice = self.ask_drivers_first()
        if choice == 'drivers':
            self.nav.setCurrentRow(1)
        return choice == 'continue'

    def ask_drivers_first(self):
        box = W.QMessageBox(self)
        box.setWindowTitle('Install drivers first (recommended)')
        box.setText('This computer has not connected to the camera successfully yet. We recommend going to the "Connection & Drivers" page first and clicking "Prepare two-stage drivers and test connection", '
                    'then coming back for the one-click install once the connection succeeds.')
        box.setInformativeText('The one-click install also tries to install drivers automatically, but a driver failure is harder to troubleshoot there. '
                               'If the driver keeps failing to install, click "Install driver manually with Zadig" on that page and follow the steps.')
        go = box.addButton('Install drivers first', W.QMessageBox.AcceptRole)
        box.addButton('One-click install now', W.QMessageBox.DestructiveRole)
        cancel = box.addButton(W.QMessageBox.Cancel)
        box.setDefaultButton(go)
        box.exec()
        return 'drivers' if box.clickedButton() is go else 'cancel' if box.clickedButton() is cancel else 'continue'

    def driver_step_failed(self, action):
        if action in ('usb_prepare', 'connect', 'driver_install'):
            return True
        if action != 'setup_all':
            return False
        try:
            state = json.loads(Path(self.settings.get('setup_work', ''), 'setup.private.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return False
        return 'drivers' not in state.get('completed_steps', [])

    def direct_verify_args(self, group, accepted=False):
        workspace=self.settings.get(group + '_direct_work', '')
        args={'workspace': workspace, 'accepted': accepted}
        if group=='factory':args.update(factory_verify=True,factory_preferred=self.text('factory_failed_work'))
        return args

    def show_setup_result(self):
        from .completion import archive_error,text
        path=Path(self.settings.get('setup_work',''),'setup.private.json')
        if not path.is_file():return
        state=json.loads(path.read_text(encoding='utf-8'))
        if state.get('phase')!='COMPLETE':
            W.QMessageBox.information(self,'Installation not finished','Click "Continue installation" on the Home page and follow the prompts to finish the remaining steps.')
            return
        if archive_error(state):write_json(path,state)
        W.QMessageBox.information(self,'Installation complete',text(state))

    def refresh_setup_controls(self):
        path=Path(self.settings.get('setup_work',''),'setup.private.json')
        state=json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
        pending=bool(state) and state.get('phase')!='COMPLETE'
        self.setup_button.setText('Continue installation' if pending else 'Start a new one-click install' if state else 'One-click install')
        self.setup_result_button.setVisible(state.get('phase')=='COMPLETE')
        self.setup_note.setVisible(pending)
        self.setup_custom_container.setEnabled(not pending and not self.setup_presets.isChecked() and self.process is None)
        if not state:
            self.setup_preset_summary.setText(presets.SUMMARY)
            self.setup_preset_summary.setEnabled(self.setup_presets.isChecked())
        for box in (self.setup_presets,self.setup_fl23,self.setup_sound,self.setup_vertical,self.setup_plugin):
            box.setEnabled(not pending and self.process is None)

    def clear_installation_state(self, verified=True):
        # Clear active navigation/resume pointers, not diagnostic evidence or
        # user source files. A verified factory reset invalidates these plans.
        # Before verification only the sound records are retired: the restore
        # has already returned every sound program window to stock.
        if verified:
            for key in ('setup_work','fl23_direct_work','look_direct_work',
                        'look_resume_source','look_job_dir'):
                self.settings.pop(key,None)
            self._look_displayed_pending=None
            self.look_editor.set_operations([])
            self.fl23_accept.setChecked(False)
        self.sound_accept.setChecked(False)
        # The old sound workspace describes the pre-reset camera installation.
        # Start fresh while retaining its files and the selected source clip.
        sound=self.work('sound')
        for key,value in (('sound_work',sound),('sound_backup',sound+'-backup')):
            self.fields[key].setText(value);self.settings[key]=value
        write_json(data_root()/'desktop.json',self.settings)
        self.log.appendPlainText('Factory restore verified; old installation state cleared. Past diagnostic logs are kept; a new installation starts from scratch.' if verified else
                                 'Factory restore write complete; the old sound records are retired (files kept), so later sound operations are no longer affected by them.')

    def reload_controls(self, layout, checks):
        guide = W.QPushButton('How to power-cycle? View detailed steps')
        guide.clicked.connect(lambda: self.show_reload_guide())
        layout.addWidget(guide)
        self.buttons.append(guide)
        # QCheckBox text never wraps; explicit breaks keep the English text inside the minimum window width.
        confirm = W.QCheckBox('Unplugged USB, waited for the lamp to stop, powered off,\nremoved the battery for at least 1 minute and restarted;\nconfirmed: ' + checks)
        confirm.setToolTip(reloadguide.text())
        layout.addWidget(confirm)
        return confirm

    def show_reload_guide(self, *, setup=False, mode=None):
        title = ('Restore not started — power-cycle and retry' if mode=='factory_prewrite_temporary' else
                 'Restore not finished — verify after restart' if mode=='factory_reset' else
                 'Audition recorded — power-cycle to restore the original sound' if mode=='sound_confirm' else 'Reads and writes finished — power-cycle the camera')
        W.QMessageBox.information(self, title, reloadguide.text(setup=setup, mode=mode))

    def show_connection_notice(self):
        W.QMessageBox.information(self,connectionguide.TITLE,connectionguide.TEXT)

    def field(self, form, key, label, *, kind=None, filter='All files (*)', value=''):
        line = W.QLineEdit(str(self.settings.get(key, value)))
        line.setObjectName(key)
        self.fields[key] = line
        if kind:
            row = W.QHBoxLayout()
            row.addWidget(line, 1)
            button = W.QPushButton('Choose…')
            button.clicked.connect(lambda: self.browse(line, kind, filter))
            row.addWidget(button)
            form.addRow(label, row)
        else:
            form.addRow(label, line)
        return line

    def browse(self, field, kind, filter):
        if kind == 'folder':
            path = W.QFileDialog.getExistingDirectory(self, 'Choose folder', field.text())
        elif kind == 'save':
            path = W.QFileDialog.getSaveFileName(self, 'Save file', field.text(), filter)[0]
        else:
            path = W.QFileDialog.getOpenFileName(self, 'Choose file', field.text(), filter)[0]
        if path:
            field.setText(path)

    def button(self, layout, text, action, arguments=lambda: {}, *, primary=False):
        button = W.QPushButton(text)
        button.setObjectName('action_' + action)
        button.setProperty('primary', primary)
        button.clicked.connect(lambda: self.launch(action, arguments()))
        layout.addWidget(button)
        self.buttons.append(button)
        return button

    def text(self, key):
        return self.fields[key].text().strip()

    def common(self):
        return {'firmware': self.firmware.currentText()}

    def work(self, label):
        return str(data_root() / 'work' / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + label + '-' + uuid.uuid4().hex[:5]))

    def connection_page(self):
        layout = self.page('Connection & Drivers', 'Turn the camera on and select Mass Storage, and use a data-capable USB cable. Connect only one camera at a time.')
        form = self.box(layout, 'USB connection')
        self.driver_identity = W.QComboBox()
        self.driver_identity.addItems(['Normal connection · 054C:0E8A', 'Service connection · 054C:0336'])
        form.addRow('Driver target', self.driver_identity)
        if sys.platform == 'darwin':
            self.field(form, 'mac_volume', 'macOS camera volume', kind='folder', value='/Volumes/')
        self.button(layout, 'Detect camera and drivers', 'driver_scan', primary=True)
        if sys.platform == 'win32':
            # Manual Zadig installation sits beside the automatic one: many
            # computers where the automatic install fails succeed with it.
            drivers = W.QHBoxLayout()
            layout.addLayout(drivers)
            # Side-by-side buttons: short labels (as referenced in messages) keep the row within the minimum width.
            self.button(drivers, 'Prepare two-stage drivers and test connection', 'usb_prepare', primary=True).setToolTip('Automatic')
            zadig = W.QPushButton('Install driver manually with Zadig')
            zadig.setToolTip('Use this if the automatic driver preparation fails')
            zadig.setObjectName('zadig_guide')
            zadig.setProperty('primary', True)
            zadig.clicked.connect(self.show_zadig_guide)
            drivers.addWidget(zadig)
            self.buttons.append(zadig)
        else:
            self.button(layout, 'Prepare USB service connection', 'usb_prepare', primary=True)
        self.button(layout, 'Install driver for the selected identity only (advanced)' if sys.platform == 'win32'
                    else 'Check USB access (macOS needs no Zadig)', 'driver_install',
                    lambda: {'pid': ['0e8a', '0336'][self.driver_identity.currentIndex()]})
        if sys.platform == 'darwin':
            self.button(layout, 'Eject the selected camera volume', 'mac_unmount', lambda: {'volume': self.text('mac_volume')})
        self.button(layout, 'Test service connection (no firmware write)', 'connect')
        self.button(layout, 'Check USB connection stability (read-only)', 'usb_stability')
        if sys.platform == 'win32':
            self.button(layout, 'Uninstall camera drivers and restore Windows default connection', 'driver_uninstall',
                        lambda: {'pids': ['0e8a', '0336']})
        hint = W.QLabel('If the connection drops, check the full log first. Errors never trigger a re-flash or an automatic driver reinstall.')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()

    def recovery_page(self):
        layout = self.page('Factory Restore', 'The factory 2.01 reference for the regions this project modifies is built in. Removes the supported project modifications, resets the six custom slots to the ST default and keeps the body calibration. No old backup or full firmware download needed; old recipes are not recovered.')
        self.factory_button=self.button(layout, 'Restore / continue restoring factory 2.01 functions (no old backup needed)', 'direct_factory_reset',
                    lambda: self.direct_args('factory', mode='factory_reset', factory='builtin'), primary=True)
        self.factory_status=W.QLabel('After the restore write you must restart as the dialog describes, then reconnect to verify; the restore is not marked complete until verification passes.')
        self.factory_status.setWordWrap(True);layout.addWidget(self.factory_status)
        resume_section = self.advanced(layout, 'Restore transaction (detected automatically; can also be chosen manually)')
        resume_form = W.QFormLayout()
        self.field(resume_form, 'factory_failed_work', 'Restore transaction folder (usually automatic)', kind='folder',
                   value=self.settings.get('factory_direct_work', ''))
        resume_section.addLayout(resume_form)
        self.factory_accept = self.reload_controls(layout, 'live view, photos and playback work normally')
        self.button(layout, 'Verify after restart and finish restore (required after a restore write)', 'direct_verify',
                    lambda: self.direct_verify_args('factory', self.factory_accept.isChecked()))
        service_note = W.QLabel('The camera must still be able to enter USB service communication; this is not a downgrade re-flash with the Sony updater.')
        service_note.setWordWrap(True); layout.addWidget(service_note)
        expert = self.advanced(layout, 'Import a complete factory 2.01 reference file (advanced, optional)')
        reference = self.box(expert, 'Factory file')
        self.field(reference, 'factory_file', 'Sony BODYDATA.DAT', kind='file', filter='Sony firmware (*.DAT *.bin);;All files (*)')
        self.button(expert, 'Prepare the selected factory file (does not connect the camera)', 'factory_prepare',
                    lambda: {'source': self.text('factory_file') or str(data_root() / 'factory-2.01')})
        self.button(expert, 'Restore using the imported complete factory file', 'direct_factory_reset',
                    lambda: self.direct_args('factory', mode='factory_reset', factory=str(data_root() / 'factory-2.01')))
        legacy = self.advanced(layout, 'Return to an earlier state from an old backup (optional)')
        self.backup_recovery_controls(legacy)
        layout.addStretch()
        self.refresh_factory_controls()

    def refresh_factory_controls(self):
        work=self.settings.get('factory_direct_work') or self.text('factory_failed_work')
        path=Path(work,'direct.private.json') if work else None
        try:state=json.loads(path.read_text(encoding='utf-8')) if path and path.is_file() else {}
        except (OSError,ValueError):return
        phase=state.get('phase')
        if phase=='AWAITING_RELOAD':
            self.factory_button.setText('Verify after restart and finish restore')
            self.factory_status.setText('Restore not finished yet: writing and readback have ended. Power-cycle the camera, reconnect USB, then click the button above to verify.')
        elif phase in ('LOADED','COMPLETE') and state.get('readonly_after_reload_verified'):
            self.factory_button.setText('Restore factory 2.01 functions again (no old backup needed)')
            self.factory_status.setText('The last restore verification passed. Program, settings, loaded state and read-only mount were verified; check current functions and shooting on the camera itself.')
        elif phase=='NEEDS_REVIEW':
            from looktool.factoryrecover import connection_failed_before_restore,prewrite_temporary_conflict
            if prewrite_temporary_conflict(state):
                self.factory_button.setText('Retry restore after power cycle (nothing written yet)')
                self.factory_status.setText('Nothing has been written for this restore yet; a temporary file conflict on the camera was found. Power-cycle completely as the dialog describes, reconnect USB, then click the button above to retry; no old LUT record is needed.')
                return
            if connection_failed_before_restore(state):
                self.factory_button.setText('Restore factory 2.01 functions (last attempt did not start)')
                self.factory_status.setText('Last time stopped at the USB connection stage; no restore write had started. Click the button above and reconnect after completing system authorization.')
                return
            self.factory_button.setText('Continue restore / verify the unfinished transaction')
            self.factory_status.setText('Restore not finished yet; continue with the unfinished transaction. The current state does not mean the restore succeeded.')

    def backup_recovery_controls(self, layout):
        form = self.box(layout, 'Restore source')
        self.field(form, 'restore_backup', 'Backup folder', kind='folder')
        choose_zip = W.QPushButton('Or choose a complete backup ZIP…')
        choose_zip.clicked.connect(lambda: self.browse(self.fields['restore_backup'], 'file', 'Backup (*.zip);;All files (*)'))
        form.addRow('', choose_zip)
        self.field(form, 'restore_work', 'Restore task folder', kind='folder', value=self.work('recovery'))
        self.button(layout, 'Inspect the selected backup (offline)', 'backup_inspect', lambda: {'backup': self.text('restore_backup')})
        auto = W.QPushButton('One-click restore: find and use the earliest complete backup')
        auto.setObjectName('one_click_restore')
        auto.clicked.connect(self.one_click_restore)
        self.buttons.append(auto)
        layout.addWidget(auto)
        self.button(layout, 'Restore the selected backup with full readback', 'restore', lambda: dict(self.common(),
            backup=self.text('restore_backup'), workspace=self.text('restore_work')), primary=True)
        self.recovery_accept = self.reload_controls(layout, 'live view, photos and playback work normally after the restore')
        self.button(layout, 'Verify loaded state after an old-backup restore', 'restore_verify', lambda: {
            'workspace': self.text('restore_work'), 'accepted': self.recovery_accept.isChecked()})
        note = W.QLabel('The camera must still be able to enter service communication. This option uses a body backup; the official BODYDATA.DAT is never flashed as a backup.')
        note.setWordWrap(True)
        layout.addWidget(note)

    def fl23_page(self):
        layout = self.page('FL2 / FL3', 'Enable or remove directly; no backup required. Removing only hides the FL2/FL3 list entries and keeps the shared color code that custom looks need; you can enable them again later.')
        self.button(layout, 'Enable / re-enable FL2 / FL3', 'direct_fl23_enable',
                    lambda: self.direct_args('fl23', mode='fl23_enable'), primary=True)
        self.button(layout, 'Remove FL2 / FL3 from the list, keep custom looks', 'direct_fl23_disable',
                    lambda: self.direct_args('fl23', mode='fl23_disable'))
        info = W.QLabel('After writing and readback, power-cycle as the dialog describes and confirm on the camera; no need to reconnect the computer to verify.')
        info.setWordWrap(True); layout.addWidget(info)
        diagnostic = self.advanced(layout, 'Load verification (optional diagnostic, not required for use)')
        self.fl23_accept = self.reload_controls(diagnostic, 'menus, photos and playback work normally')
        self.button(diagnostic, 'Read-only check of the loaded version (optional)', 'direct_verify',
                    lambda: self.direct_verify_args('fl23', self.fl23_accept.isChecked()))
        layout.addStretch()

    def look_page(self):
        from .lookeditor import LookEditor
        layout=self.page('Custom Creative Looks','Add only the slots you want to change; slots not added stay unchanged. One batch can both write looks and restore ST defaults.')
        self.look_pending=W.QLabel();self.look_pending.setWordWrap(True);layout.addWidget(self.look_pending)
        self.look_editor=LookEditor();layout.addWidget(self.look_editor)
        self.look_button=W.QPushButton('Add an operation to continue');self.look_button.setProperty('primary',True)
        self.look_button.setObjectName('action_direct_looks_import');self.look_button.clicked.connect(self.launch_look_changes)
        layout.addWidget(self.look_button);self.buttons.append(self.look_button)
        tools=W.QHBoxLayout();layout.addLayout(tools)
        for title,callback in [('Open built-in DCP/A7Look pair library',self.open_profile_library),('Generate A7Look from DCP/LUT…',self.compiler_dialog),('Install LrC plug-in…',self.plugin_dialog)]:
            button=W.QPushButton(title);button.clicked.connect(callback);tools.addWidget(button);self.buttons.append(button)
        formats=W.QPushButton('LUT format guide: ST / sRGB, not S-Log3…')
        formats.clicked.connect(self.show_look_format_guide);layout.addWidget(formats);self.buttons.append(formats)
        writes_note=W.QLabel('This page writes .a7look files; convert .cube / .dcp with the tools above first. Only slots in the list are changed.')
        writes_note.setWordWrap(True);layout.addWidget(writes_note)
        hint=W.QLabel('One operation checks the current state, writes and fully reads back automatically. Afterwards power-cycle as the dialog describes to load; no separate verification click needed.')
        hint.setWordWrap(True);layout.addWidget(hint)
        layout.addStretch()
        self._look_displayed_pending=None;self._look_refreshing=False
        self.look_editor.changed.connect(self.refresh_look_controls)
        self.refresh_look_controls()

    def open_profile_library(self):
        from .profilelibrary import location
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(location())))

    def look_pending_state(self):
        prior=self.settings.get('look_direct_work')
        if not prior:return None
        try:
            job=self.settings.get('look_job_dir')
            if job and Path(job,'status.private.json').is_file():
                status=json.loads(Path(job,'status.private.json').read_text(encoding='utf-8'))
                request=json.loads(Path(job,'request.private.json').read_text(encoding='utf-8'))
                matches=prior in (request.get('arguments',{}).get('workspace'),status.get('result',{}).get('workspace'))
                if matches and status.get('phase')=='SUCCEEDED':
                    prior=status['result']['workspace']
                elif matches and status.get('phase') in ('RUNNING','QUEUED') and self.process is None:
                    return prior,dict(phase='BACKGROUND_UNCONFIRMED',error='The background task has not been confirmed as finished; wait for its result or check the log. Nothing will be written again.')
            if not Path(prior,'direct.private.json').is_file():
                prior=self.settings.get('look_resume_source')
                if not prior or not Path(prior,'direct.private.json').is_file():return None
            state=json.loads(Path(prior,'direct.private.json').read_text(encoding='utf-8'))
            nested=Path(prior,'program-install/direct.private.json')
            if state.get('phase')=='RESOURCE_RELOAD_VERIFIED' and nested.is_file():
                prior=str(nested.parent);state=json.loads(nested.read_text(encoding='utf-8'))
        except (ValueError,OSError,KeyError) as exc:return str(prior),dict(phase='UNREADABLE',error=str(exc))
        return None if state.get('phase') in ('AWAITING_RELOAD','LOADED','COMPLETE') else (prior,state)

    def refresh_look_controls(self):
        if self._look_refreshing:return
        self._look_refreshing=True
        try:
            pending=self.look_pending_state();busy=self.process is not None
            if pending:
                prior,state=pending;phase=state.get('phase')
                token=(prior,phase)
                if self._look_displayed_pending!=token:
                    options=state.get('bundle_options',{});by_slot={r['slot']:r for r in options.get('looks',[])}
                    operations=options.get('slot_operations') or [dict(r,action='write') for r in by_slot.values()]+[dict(slot=n,action='restore') for n in options.get('reset_slots',[])]
                    if not operations and state.get('mode')=='slot_default':operations=[dict(slot=state['slot'],action='restore')]
                    if not operations and state.get('mode')=='look_import':operations=[dict(slot=state['slot'],action='write',path=str(Path(prior)/'reference.a7look'),name=state.get('name') or '')]
                    operations=[dict(r,**{k:v for k,v in by_slot.get(r['slot'],{}).items() if k!='slot'}) if r.get('action')=='write' else r for r in operations]
                    self.look_editor.set_operations(operations);self._look_displayed_pending=token
                self.look_editor.setEnabled(False);self.look_button.setEnabled(not busy)
                if phase in ('AWAITING_RESOURCE_RELOAD','RESOURCE_RELOAD_VERIFIED') or (phase=='NEEDS_REVIEW' and state.get('forward_name_build',{}).get('stream_install') and 'readonly=-16' in state.get('error','')):
                    text='The previous operation is waiting to resume after the resource reload and will reuse the saved list.'
                    self.look_button.setText('Continue slot changes')
                else:
                    from .lookbatch import read_only_failure
                    if read_only_failure(state):
                        text='Last time stopped before writing; the old record is kept. You can adjust the list and retry.'
                        self.look_editor.setEnabled(not busy)
                        self.look_button.setText('Retry these changes (nothing written last time)')
                        self.look_button.setEnabled(not busy and bool(self.look_editor.values()) and not self.look_editor.errors())
                    else:
                        text='The previous operation has not finished; check the original task record. Nothing is written again automatically.'
                        self.look_button.setText('View unfinished task record')
                self.look_pending.setText(text);self.look_pending.show()
            else:
                if self._look_displayed_pending is not None:
                    self._look_displayed_pending=None;self.look_editor.set_operations([])
                self.look_pending.hide();self.look_editor.setEnabled(not busy)
                rows=self.look_editor.values()
                self.look_button.setText('Review and apply these %d change(s)'%len(rows) if rows else 'Add an operation to continue')
                self.look_button.setEnabled(bool(rows) and not self.look_editor.errors() and not busy)
        finally:self._look_refreshing=False

    def look_batch_args(self):
        return self.direct_args('look',operations=self.look_editor.values())

    def launch_look_changes(self):
        pending=self.look_pending_state()
        if pending:
            prior,state=pending;phase=state.get('phase')
            if phase in ('AWAITING_RESOURCE_RELOAD','RESOURCE_RELOAD_VERIFIED') or (phase=='NEEDS_REVIEW' and state.get('forward_name_build',{}).get('stream_install') and 'readonly=-16' in state.get('error','')):
                self.launch('direct_resume_looks',dict(self.common(),workspace=self.work('look'),failed_workspace=prior));return
            from .lookbatch import read_only_failure
            if read_only_failure(state):
                self.launch('direct_looks_import',self.look_batch_args());return
            W.QMessageBox.warning(self,'Previous task not finished',state.get('error','Keep the original record and check the unknown result before continuing.')+'\nTask folder: '+prior)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(prior));return
        self.launch('direct_looks_import',self.look_batch_args())

    def vertical_page(self):
        layout = self.page('Vertical Display', 'When the camera is held vertically, shooting info, icons and layout rotate with it. Turning it on saves the native switch and takes effect automatically after a power cycle; the full MENU does not rotate.')
        form = self.box(layout, 'Display task')
        self.field(form, 'vertical_work', 'Task folder', kind='folder', value=str(data_root() / 'vertical'))
        args = lambda: dict(self.common(), workspace=self.text('vertical_work'))
        self.button(layout, 'Turn on Vertical Display', 'vertical_enable', args, primary=True)
        self.button(layout, 'Turn off Vertical Display', 'vertical_disable', args)
        frame_hint=W.QLabel('Turning on saves the vertical switch and applies the current Fn/submenu display fixes; turning off first disables vertical display, then reverts the display fixes. Both can safely be repeated.')
        frame_hint.setWordWrap(True);layout.addWidget(frame_hint)
        known=W.QLabel('Known display issues: in vertical orientation the outer frame of the Creative Look selection page is still too thick; the scale is now shown horizontally, but the orange pointer direction is not fixed yet.')
        known.setWordWrap(True);layout.addWidget(known)
        hint = W.QLabel('Turning on/off completes the selected writes and readback in one go, then a single dialog asks you to power-cycle to load. Clicking again in the same state is fine; identical content is not written again.')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()

    def sound_page(self):
        layout = self.page('Electronic Shutter Sound', 'A separate switch controls the electronic shutter sound path. A converted clip can be saved directly; a temporary audition is optional. After writing, power-cycle as the dialog describes to load.')
        form = self.box(layout, 'Sound workspace')
        self.field(form, 'sound_work', 'Work folder', kind='folder', value=str(data_root() / 'sound'))
        self.field(form, 'sound_backup', 'Second backup', kind='folder', value=str(data_root() / 'sound-backup'))
        args = lambda: dict(self.common(), workspace=self.text('sound_work'), backup=self.text('sound_backup'))
        row = W.QHBoxLayout()
        layout.addLayout(row)
        self.button(row, 'Enable electronic shutter sound', 'sound_on', args)
        self.button(row, 'Disable electronic shutter sound', 'sound_off', args)
        media = self.box(layout, 'Import audio/video clip')
        self.field(media, 'sound_source', 'Sound file', kind='file', filter='Audio / video (*.wav *.mp3 *.mp4 *.m4a *.flac *.ogg);;All files (*)')
        self.sound_start = W.QDoubleSpinBox()
        self.sound_start.setRange(0, 86400)
        self.sound_start.setDecimals(3)
        media.addRow('Start (s)', self.sound_start)
        self.sound_duration = W.QDoubleSpinBox()
        self.sound_duration.setRange(.01, 2)
        self.sound_duration.setDecimals(3)
        self.sound_duration.setValue(.5)
        media.addRow('Length (s)', self.sound_duration)
        row = W.QHBoxLayout()
        layout.addLayout(row)
        self.button(row, 'Convert selected clip', 'sound_import', lambda: dict(args(), source=self.text('sound_source'),
            start=self.sound_start.value(), duration=self.sound_duration.value(), peak=.4))
        self.button(row, 'Temporary in-camera audition', 'sound_audition', args)
        volume = W.QHBoxLayout()
        layout.addLayout(volume)
        self.button(volume, 'Volume −3 dB', 'sound_volume', lambda: dict(args(), decibels=-3))
        self.button(volume, 'Volume +3 dB', 'sound_volume', lambda: dict(args(), decibels=3))
        self.button(volume, 'Reset to converted volume', 'sound_volume', lambda: dict(args(), reset=True))
        volume_hint=W.QLabel('Convert a clip first, then adjust the volume; this only processes audio on the computer and does not connect the camera. At the volume limit, gain is capped automatically to avoid clipping; saving uses the adjusted sound. Converting again resets the volume.')
        volume_hint.setWordWrap(True);layout.addWidget(volume_hint)
        self.button(layout, 'Save current custom sound', 'sound_install', args, primary=True)
        hint=W.QLabel('Once converted, the clip can be saved directly; the workspace and electronic shutter sound support are prepared automatically, with no need to turn it on first or link an old task. The audition is optional; after all writes finish, power-cycle once as the dialog describes to load.')
        hint.setWordWrap(True);layout.addWidget(hint)
        optional=self.advanced(layout,'Audition confirmation and restore record (optional, does not affect saving)')
        self.button(optional, 'Confirm audition is correct', 'sound_confirm', lambda: dict(args(), result='correct'))
        self.button(optional, 'Power-cycled to restore original sound; record restore complete', 'sound_confirm_recovery', args)
        self.sound_accept = self.reload_controls(layout, 'sound is correct, shooting and playback work normally')
        self.button(layout, 'Verify sound after restart', 'sound_verify', lambda: dict(args(), accepted=self.sound_accept.isChecked()))
        self.button(layout, 'Restore factory sound', 'sound_restore_sound', args)
        layout.addStretch()

    def show_zadig_guide(self):
        from .zadigguide import TITLE, TEXT, URL
        dialog = W.QDialog(self); dialog.setWindowTitle(TITLE); dialog.resize(820, 680)
        layout = W.QVBoxLayout(dialog)
        content = W.QTextBrowser(); content.setPlainText(TEXT); layout.addWidget(content)
        row = W.QHBoxLayout(); layout.addLayout(row)
        download = W.QPushButton('Open Zadig download page'); download.setProperty('primary', True)
        download.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(URL)))
        close = W.QPushButton('Close'); close.clicked.connect(dialog.accept)
        row.addWidget(download); row.addWidget(close)
        dialog.exec()

    def show_look_format_guide(self):
        from .lookguide import TITLE,TEXT
        dialog=W.QDialog(self);dialog.setWindowTitle(TITLE);dialog.resize(800,650)
        layout=W.QVBoxLayout(dialog)
        content=W.QTextBrowser();content.setPlainText(TEXT);layout.addWidget(content)
        close=W.QPushButton('Close');close.clicked.connect(dialog.accept);layout.addWidget(close)
        dialog.exec()

    def compiler_dialog(self):
        dialog = W.QDialog(self)
        dialog.setWindowTitle('Generate A7Look')
        dialog.resize(760, 370)
        layout = W.QVBoxLayout(dialog)
        hint = W.QLabel('CUBE: input must be Sony ST / sRGB and output sRGB; S-Log3 / S-Gamut3.Cine or other Log LUTs cannot be used directly.\nDCP: parsed and fitted offline with the built-in tools; no Lightroom, plug-in or network needed. The LookTable / tone curve is converted, and the in-camera result is a fitted approximation. This tool only generates .a7look files and does not write to the camera.')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        help_button=W.QPushButton('Which formats and color spaces are supported? View the full guide…')
        help_button.clicked.connect(self.show_look_format_guide);layout.addWidget(help_button)
        form = self.box(layout, 'Source and output')
        self.field(form, 'compile_source', 'DCP / CUBE', kind='file', filter='Reference (*.dcp *.cube)')
        self.field(form, 'compile_name', 'Look name')
        self.field(form, 'compile_output', 'Output A7Look', kind='save', filter='A7Look (*.a7look)')
        self.field(form, 'compile_model', 'Response file', kind='file', filter='Response (*.npz)',
                   value=str(ROOT / 'calibration/a7c2-2.01.virtual.npz'))
        run = W.QPushButton('Generate')
        run.clicked.connect(lambda: (dialog.accept(), self.launch('compile_look', {
            'source': self.text('compile_source'), 'name': self.text('compile_name'),
            'output': self.text('compile_output'), 'model': self.text('compile_model'),
            'input_space': 'sony-st-srgb', 'passes': 3})))
        layout.addWidget(run)
        dialog.exec()

    def plugin_dialog(self):
        self.launch('plugin_install', {})

    def one_click_restore(self):
        roots = [str(data_root() / 'backups'), str(data_root() / 'initial-checkpoints')]
        for key in ('fl23_backup', 'look_backup', 'restore_backup'):
            if key in self.fields and self.text(key):
                roots.append(self.text(key))
        self.fields['restore_work'].setText(self.work('recovery'))
        self.launch('restore_auto', dict(self.common(), roots=roots, workspace=self.text('restore_work')))

    def launch(self, action, arguments):
        if self.process is not None:
            return
        factory_finished = False
        if action == 'setup_all' and not self.drivers_first(arguments):
            return
        if action=='direct_looks_import' and arguments.get('failed_workspace'):
            action='direct_resume_looks'
        if action=='direct_looks_import':
            try:
                from .worker import setup_runtime
                setup_runtime()
                from .lookbatch import options
                chosen=options(arguments.get('operations',arguments.get('looks',[])))
                arguments=dict(arguments,operations=chosen['slot_operations'])
            except (ValueError,OSError,KeyError,TypeError) as exc:
                W.QMessageBox.warning(self,'Check the operation list',str(exc));return
        if action == 'sound_audition':
            from .actions.sound import has_conversion
            try:
                ready = has_conversion(arguments['workspace'])
            except (ValueError, OSError, KeyError) as exc:
                W.QMessageBox.warning(self, 'Sound workspace needs checking', str(exc));return
            if not ready:
                W.QMessageBox.information(self, 'Convert a clip first', 'There is no converted sound yet. Choose a sound file, set the start and length, click "Convert selected clip", and audition after it succeeds.');return
        if action == 'restore_verify' and not Path(arguments.get('workspace', ''), 'rollback.private.json').is_file():
            # This button checks a backup restore only. A built-in or firmware
            # file restore is checked by the factory verification button.
            answer = W.QMessageBox.question(self, 'No old-backup restore record here',
                '"Verify loaded state after an old-backup restore" is only for "Return to an earlier state from an old backup".\n'
                'After restoring from the built-in factory reference or a firmware file, click "Verify after restart and finish restore".\nVerify the factory restore instead now?',
                W.QMessageBox.Yes | W.QMessageBox.Cancel, W.QMessageBox.Yes)
            if answer != W.QMessageBox.Yes:
                return
            action, arguments = 'direct_verify', self.direct_verify_args('factory', bool(arguments.get('accepted')))
        if action == 'direct_factory_reset':
            # A failed fresh attempt must not hide the original interrupted
            # transaction. Resolve the explicitly selected evidence locally,
            # before the power/write confirmation and before any USB access.
            from .worker import setup_runtime
            setup_runtime()
            from looktool.factoryrecover import pending, FINISHED
            try:
                found = pending(data_root() / 'work', self.text('factory_failed_work'))
            except (ValueError, OSError):
                found = None  # Records are evidence only; the worker re-plans.
            if found:
                # A finished restore is verified first; the worker re-plans
                # from current bytes if the camera changed since then.
                original, prior = found
                factory_finished = prior['phase'] in FINISHED
                action = 'direct_resume_factory'
                arguments = dict(arguments, failed_workspace=str(original), accepted=self.factory_accept.isChecked())
        if action == 'driver_uninstall':
            answer = W.QMessageBox.question(self, 'Uninstall camera drivers',
                'This backs up and uninstalls the third-party drivers for Sony 054C:0E8A/0336 so Windows re-detects the camera.\n'
                'Afterwards you may need to unplug and replug USB and select Mass Storage mode again. This does not change the camera firmware.\nUninstall now?',
                W.QMessageBox.Yes | W.QMessageBox.Cancel, W.QMessageBox.Cancel)
            if answer != W.QMessageBox.Yes:
                return
        writing = action in jobs.POWER_ACTIONS
        if writing:
            target = (('features ticked on the Home page; replaces Custom 1–6: ' + presets.SUMMARY if arguments.get('options', {}).get('preset_pack') else 'features ticked on the Home page and the selected A7Look slots') if action == 'setup_all' else
                      'automatically choose the earliest available complete backup of the connected body' if action == 'restore_auto' else
                      arguments.get('backup') if action == 'restore' else arguments.get('look') or arguments.get('workspace'))
            if action in jobs.DIRECT_ACTIONS:
                target = ('; '.join('Custom %s → %s' % (r['slot'], 'restore ST default' if r['action']=='restore' else 'write '+r['name']) for r in arguments.get('operations', []))
                          if action == 'direct_looks_import' else
                          'continue the look installation whose names are already written: '+arguments.get('failed_workspace','') if action=='direct_resume_looks' else
                          ('verify the last restore; if the camera contents changed, restore again from the current bytes: ' if factory_finished else
                           'continue the name/settings restore: ') + arguments.get('failed_workspace', '') if action == 'direct_resume_factory' else
                          'Vertical Display + Fn/submenu frame fixes' if action=='vertical_enable' else
                          'turn off Vertical Display and revert the frame fixes' if action=='vertical_disable' else
                          'factory 2.01 functions' if action == 'direct_factory_reset' else
                          'FL2/FL3: enable' if action == 'direct_fl23_enable' else
                          'FL2/FL3: remove from list' if action == 'direct_fl23_disable' else
                          'Custom %s: %s' % (arguments.get('slot'), 'ST default' if action == 'direct_slot_default'
                                           else arguments.get('name') or Path(arguments.get('look', '')).stem))
            scope = ('Applies the writes and restores in the list in one go; slots not added stay unchanged, and FL23, sound and vertical display are kept. After writing and readback, you will be asked once to power-cycle.\n' if action=='direct_looks_import' else
                     'Prepares drivers automatically and installs the features ticked on the Home page. You must do the power cycle yourself when prompted; if a result is unclear the process stops and never re-flashes automatically.\n' if action == 'setup_all' else
                     'Verifies read-only first; it writes from the current bytes only if the camera contents have changed, and content already at factory state is not written again.\n' if action == 'direct_resume_factory' and factory_finished else
                     'Continues the unfinished stage from the current bytes; restored content is not written again. The original failed transaction is kept, and if a result is unclear the report is read and checked first.\n' if action == 'direct_resume_factory' else
                     'Removes the project program modifications and resets the six custom slots to the ST default; old recipes are not recovered. Select ST on the camera first.\n' if action == 'direct_factory_reset' else
                     'Only hides the FL2/FL3 list entries, keeping the LUTs and shared code. Select ST on the camera first.\n' if action == 'direct_fl23_disable' else
                     'Resets the selected custom slot to the ST default and keeps the other slots.\n' if action == 'direct_slot_default' else '')
            answer = W.QMessageBox.question(self, 'Start camera write',
                scope + 'Target: ' + str(target) + '\nConfirm the body is an ILCE-7CM2 on firmware 2.01 with enough battery (at least 50% recommended).\n'
                'Firmware modified by other projects may conflict with this tool.\n'
                'Keep power and the USB connection during the operation and full readback; do not power off or unplug.\nPower is sufficient — start now?',
                W.QMessageBox.Yes | W.QMessageBox.Cancel, W.QMessageBox.Cancel)
            if answer != W.QMessageBox.Yes:
                return
            arguments = dict(arguments, power_confirmed=True)
            arguments.pop('battery', None)
        if action in jobs.DIRECT_ACTIONS:
            group = 'factory' if action in ('direct_factory_reset', 'direct_resume_factory') else 'fl23' if 'fl23' in action else 'look'
            self.settings[group + '_direct_work'] = arguments['workspace']
            if group=='look':
                self.settings['look_resume_source']=arguments.get('failed_workspace','')
            if group!='look':getattr(self, group + '_accept').setChecked(False)
        if action == 'setup_all':
            self.settings['setup_work'] = arguments['workspace']
            self.setup_button.setText('Installing…')
            for box in (self.setup_presets,self.setup_fl23,self.setup_sound,self.setup_vertical,self.setup_plugin):box.setEnabled(False)
        for key, field in self.fields.items():
            self.settings[key] = field.text()
        write_json(data_root() / 'desktop.json', self.settings)
        self.current_job = jobs.new_job(action, arguments)
        if action in ('direct_looks_import','direct_resume_looks') or (action=='direct_verify' and arguments.get('workspace')==self.settings.get('look_direct_work')):
            self.settings['look_job_dir']=str(self.current_job)
            write_json(data_root()/'desktop.json',self.settings)
        self.log_offset = 0
        self.log.clear()
        self.camera_operation = action in jobs.CAMERA_ACTIONS or action == 'driver_install'
        for button in self.buttons:
            button.setEnabled(False)
        self.look_editor.setEnabled(False)
        self.stop.setEnabled(not self.camera_operation)
        self.progress.setRange(0, 0)
        self.status.setText('Running: ' + action + '. The detailed log is saved continuously.')
        self.process = QtCore.QProcess(self)
        self.process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        env = QtCore.QProcessEnvironment.systemEnvironment()
        env.insert('PYTHONUTF8', '1')
        env.insert('PYTHONIOENCODING', 'utf-8')
        self.process.setProcessEnvironment(env)
        command = jobs.worker_command(self.current_job / 'request.private.json')
        self.process.readyReadStandardOutput.connect(self.process_output)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.process.start(command[0], command[1:])

    def process_output(self):
        text = bytes(self.process.readAllStandardOutput()).decode('utf-8', errors='replace')
        if text:
            with (self.current_job / 'process.log').open('a', encoding='utf-8') as stream:
                stream.write(text)
            self.log.appendPlainText(text.rstrip())

    def tail_log(self):
        if not self.current_job:
            return
        path = self.current_job / 'worker.log'
        if path.exists():
            with path.open('rb') as stream:
                stream.seek(self.log_offset)
                text = stream.read()
                self.log_offset = stream.tell()
            if text:
                self.log.appendPlainText(text.decode('utf-8', errors='replace').rstrip())

    def poll_job(self):
        self.tail_log()
        if self.process is None and (self._look_displayed_pending is not None or self.look_pending_state()):self.refresh_look_controls()
        # The status file also recovers completion if Qt missed its signal.
        if self.process is not None and self.process.state() == QtCore.QProcess.NotRunning:
            self.finished(self.process.exitCode(), self.process.exitStatus())

    def finished(self, code, exit_status):
        if self.process is None:
            return
        self.tail_log()
        status_path = self.current_job / 'status.private.json'
        status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {}
        success = code == 0 and status.get('phase') == 'SUCCEEDED'
        if success and (status.get('action') in ('usb_prepare', 'connect') or
                        (status.get('action') == 'setup_all' and 'drivers' in status.get('result', {}).get('completed_steps', []))):
            self.settings['connection_verified'] = True
        if success and status.get('action') == 'restore_auto':
            self.fields['restore_backup'].setText(status['result']['backup'])
            self.fields['restore_work'].setText(status['result']['workspace'])
        if success and status.get('action') == 'look_restore' and 'look_work' in self.fields:
            self.fields['look_work'].setText(status['result']['workspace'])
        if success and status.get('action') in ('direct_factory_reset', 'direct_resume_factory'):
            self.settings['factory_direct_work'] = status['result']['workspace']
            self.fields['factory_failed_work'].setText(status['result']['workspace'])
        if success and status.get('action')=='direct_verify' and status['result'].get('mode')=='factory_reset':
            self.settings['factory_direct_work']=status['result']['workspace']
        if success and (status.get('action') in ('direct_looks_import','direct_resume_looks') or
                (status.get('action')=='direct_verify' and status['result'].get('mode') in ('install_all','look_import','slot_default'))):
            self.settings['look_direct_work']=status['result']['workspace']
            self.settings.pop('look_resume_source',None)
        if success and status.get('action') == 'setup_all':
            for key in ('sound_workspace','sound_backup'):
                target='sound_work' if key=='sound_workspace' else 'sound_backup'
                if status['result'].get(key):self.fields[target].setText(status['result'][key])
        for key, field in self.fields.items():
            self.settings[key] = field.text()
        write_json(data_root() / 'desktop.json', self.settings)
        waiting=success and reloadguide.required(status.get('action'),status.get('result',{}))
        sound_notice=reloadguide.sound_notice(status.get('action'),status.get('result',{})) if success else None
        factory_wait=success and status.get('result',{}).get('mode')=='factory_reset' and status['result'].get('phase')=='AWAITING_RELOAD'
        factory_done=success and status.get('result',{}).get('mode')=='factory_reset' and status['result'].get('phase') in ('LOADED','COMPLETE')
        if factory_done:self.clear_installation_state()
        elif factory_wait:self.clear_installation_state(verified=False)
        resource_wait=status.get('result',{}).get('phase') in ('WAIT_RESOURCE_RELOAD','AWAITING_RESOURCE_RELOAD')
        resource_ready=success and status.get('result',{}).get('phase')=='RESOURCE_RELOAD_VERIFIED'
        setup_wait=waiting and status.get('action')=='setup_all'
        self.status.setText(('Names are written; the program is not written yet. Power-cycle as the dialog describes, reconnect USB, then click "Continue installation" on the Home page.' if resource_wait and setup_wait else
                             'Names are written; the program is not written yet. Power-cycle as the dialog describes, reconnect USB, then click "Continue slot changes" on the Custom Creative Looks page.' if resource_wait else
                             'Batch look write complete and fully read back; power-cycle once as the dialog describes to load.' if status.get('action')=='direct_looks_import' else
                             'FL23 operation complete; writing and full readback have finished. It takes effect after restarting the camera; no verification click needed.' if
                             status.get('result',{}).get('mode') in ('fl23_enable','fl23_disable') else
                             'Reads and writes finished. Unplug USB → wait for the lamp to stop → power off and wait until dark → remove the battery for at least 1 minute → power on → reconnect USB → click "Continue installation" on the Home page. See the dialog for details.' if setup_wait else
                             'Reads and writes finished. Unplug USB → wait for the lamp to stop → power off and wait until dark → remove the battery for at least 1 minute → power on; see the dialog for details.') if waiting else
                           'Names and read-only mount confirmed; the program is not installed yet. Click "Continue installation" on the Home page.' if resource_ready and status.get('action')=='setup_all' else
                           'Names and read-only mount confirmed; the program is not installed yet. Click "Continue slot changes" on the Custom Creative Looks page.' if resource_ready else
                           'Done. Follow the log for the next step.' if success else
                           'Operation stopped: ' + status.get('error', 'the process exited abnormally, exit code ' + str(code)) + '. Please export a diagnostic package.')
        if not success and sys.platform == 'win32' and self.driver_step_failed(status.get('action')):
            self.status.setText(self.status.text() + DRIVER_HINT)
        if sound_notice:self.status.setText(sound_notice['status'])
        if factory_wait:self.status.setText('Restore not finished yet: writing and readback have ended. You must power-cycle, reconnect USB, then click "Verify after restart and finish restore".')
        elif factory_done:self.status.setText('Factory restore verification passed and the old installation state has been cleared. Keep checking shooting and playback on the camera; to install again, click "One-click install" on the Home page.')
        self.progress.setRange(0, 100)
        self.progress.setValue(70 if factory_wait else 0 if sound_notice and status.get('action')=='sound_install' else
                              40 if success and (resource_wait or resource_ready) else 70 if waiting and status.get('action')=='setup_all' else 100 if success else 0)
        for button in self.buttons:
            button.setEnabled(True)
        self.stop.setEnabled(False)
        self.process.deleteLater()
        self.process = None
        if success and status.get('action') in ('direct_looks_import','direct_resume_looks','direct_verify') and status.get('result',{}).get('mode') in ('install_all','look_import','slot_default') and status['result'].get('phase') in ('COMPLETED','AWAITING_RELOAD','LOADED','COMPLETE') and (status['action']!='direct_verify' or self._look_displayed_pending is not None):
            self.look_editor.set_operations([])
        self.refresh_look_controls()
        self.refresh_setup_controls()
        self.refresh_factory_controls()
        if not success and status.get('action')=='direct_factory_reset':
            from looktool.factoryrecover import prewrite_temporary_conflict
            work=self.settings.get('factory_direct_work')
            path=Path(work,'direct.private.json') if work else None
            try:state=json.loads(path.read_text(encoding='utf-8')) if path and path.is_file() else {}
            except (OSError,ValueError):state={}
            if prewrite_temporary_conflict(state) and state.get('error')==status.get('error'):
                self.status.setText('Nothing has been written for this restore yet. Power-cycle completely as the dialog describes, reconnect USB, then click "Retry restore after power cycle".')
                self.show_reload_guide(mode='factory_prewrite_temporary')
        if sound_notice:
            W.QMessageBox.information(self,sound_notice['title'],sound_notice['text'])
        elif status.get('action')=='usb_stability':
            if success:
                result=status['result']
                W.QMessageBox.information(self,'USB read-only check passed',
                    'Completed %d rounds, %.1f MB of read-only program file transfers over %.0f s, with identical bytes in every round.\n\nNo firmware or settings were written and no native write program was run.\n\n%s'%
                    (len(result['rounds']),result['total_bytes']/1024/1024,result.get('seconds',0),result['note']))
            else:
                error=status.get('error','Check the log, change the cable and test again.')
                # usbcheck reports 'incomplete' (Chinese: 未完成) separately from a failure.
                incomplete='未完成' in error or 'USB stability check incomplete' in error
                W.QMessageBox.warning(self,'USB connection check incomplete' if incomplete else 'USB connection check failed',error)
        elif waiting:
            self.show_reload_guide(setup=status.get('action')=='setup_all', mode=('resource_reload' if resource_wait else status.get('action') if
                status.get('action','').startswith('sound_') else status.get('result',{}).get('mode')))
        elif success and status.get('action')=='setup_all' and status.get('result',{}).get('phase')=='COMPLETE':
            self.status.setText('Installation complete. You can view the last installation result; no need to flash again.')
            self.setup_button.setText('Start a new one-click install')
            self.setup_result_button.setVisible(True)
            for box in (self.setup_presets,self.setup_fl23,self.setup_sound,self.setup_vertical,self.setup_plugin):box.setEnabled(True)
            self.show_setup_result()

    def process_error(self, error):
        if self.process and error == QtCore.QProcess.FailedToStart:
            self.log.appendPlainText(self.process.errorString())
            self.finished(-1, None)

    def open_job(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self.current_job or data_root())))

    def export_logs(self):
        if not self.current_job:
            return
        path = W.QFileDialog.getSaveFileName(self, 'Export diagnostics', 'a7c2-diagnostics.zip', 'ZIP (*.zip)')[0]
        if path:
            try:
                jobs.export_support(self.current_job, path)
            except Exception as exc:
                W.QMessageBox.warning(self, 'Export failed', str(exc))

    def cancel_offline(self):
        if self.process and not self.camera_operation:
            self.process.terminate()

    def closeEvent(self, event):
        if self.process:
            W.QMessageBox.information(self, 'Task still running', 'Wait for the current task to finish before closing. Do not quit the program or unplug while writing to the camera.')
            event.ignore()
        else:
            event.accept()


def main():
    app = W.QApplication.instance() or W.QApplication(sys.argv)
    if '--smoke-test' in sys.argv and sys.platform == 'win32':
        # Qt's headless test platform does not enumerate Windows system fonts.
        import os
        font = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/msyh.ttc'
        if font.is_file():
            QtGui.QFontDatabase.addApplicationFont(str(font))
    app.setApplicationName('A7C2Tools')
    app.setOrganizationName('QAQLeonard')
    window = Window()
    window.show()
    if '--smoke-test' in sys.argv:
        data_root().mkdir(parents=True, exist_ok=True)
        for index in range(window.pages.count()):
            window.nav.setCurrentRow(index)
            app.processEvents()
            if not window.grab().save(str(data_root() / ('desktop-page-' + str(index + 1) + '.png'))):
                raise OSError('Could not save desktop smoke screenshot')
        window.nav.setCurrentRow(0)
        QtCore.QTimer.singleShot(800, app.quit)
    else:
        QtCore.QTimer.singleShot(0,window.show_connection_notice)
    return app.exec()
