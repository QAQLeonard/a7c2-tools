"""Current desktop workflows, shared workers and diagnostic logging."""
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
from .disclaimer import require_consent

DRIVER_HINT = ('\n驱动或连接没有成功：先在“安装驱动”页卸载驱动后重装；仍不行，'
               '可点该页的“用 Zadig 手动安装驱动”，按说明给 0E8A 和 0336 两个身份分别装 libusbK。')
from . import connectionguide
from .paths import ROOT, data_root, load_settings, write_json
from .theme import WINDOW as STYLE, asset

NAVIGATION = (
    ('install','安装向导','firmware'),('drivers','安装驱动','driver'),
    ('trust','首次授信','trust'),('firmware','生成固件','firmware'),
    ('looks','滤镜','looks'),('sound','快门音效','sound'),
    ('recovery','一键恢复','restore'),('advanced','高级设置','connection'),
)


class TransportChoice(W.QWidget):
    changed=QtCore.Signal()

    def __init__(self,key):
        super().__init__()
        self.setObjectName(key+'Transport')
        # Drawn as a two-segment control; the exclusive checkboxes stay as-is.
        self.setProperty('segmented',True);self.setAttribute(QtCore.Qt.WA_StyledBackground,True)
        row=W.QHBoxLayout(self);row.setContentsMargins(2,2,2,2);row.setSpacing(0)
        self.usb=W.QCheckBox('USB · 线刷');self.ssh=W.QCheckBox('SSH · Wi-Fi')
        self.usb.setObjectName(key+'Usb');self.ssh.setObjectName(key+'Ssh')
        self.group=W.QButtonGroup(self);self.group.setExclusive(True)
        for index,button in enumerate((self.usb,self.ssh)):
            self.group.addButton(button,index);row.addWidget(button)
        self.usb.setChecked(True)
        self.group.idToggled.connect(lambda index,checked:self.changed.emit() if checked else None)

    def value(self):return 'ssh' if self.ssh.isChecked() else 'usb'

    def select(self,value):
        if value not in ('usb','ssh'):raise ValueError('Unknown connection choice')
        (self.ssh if value=='ssh' else self.usb).setChecked(True)


class Window(W.QMainWindow):
    def __init__(self, *, demo=False):
        super().__init__()
        self.setWindowTitle('A7C II Tools · '+VERSION)
        self.setWindowIcon(QtGui.QIcon(asset('mark.png')))
        self.resize(1180, 860)
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
        central.setObjectName('content')
        self.setCentralWidget(central)
        layout = W.QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = W.QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(228)
        side = W.QVBoxLayout(sidebar)
        side.setContentsMargins(14, 22, 14, 16)
        side.setSpacing(0)
        brand = W.QHBoxLayout()
        brand.setSpacing(10)
        brand.setContentsMargins(6, 0, 0, 0)
        mark = W.QLabel()
        mark.setPixmap(QtGui.QIcon(asset('mark.png')).pixmap(QtCore.QSize(34, 34), self.devicePixelRatioF()))
        mark.setFixedSize(34, 34)
        brand.addWidget(mark, 0, QtCore.Qt.AlignTop)
        names = W.QVBoxLayout()
        names.setSpacing(1)
        brand_name = W.QLabel('A7C II Tools')
        brand_name.setObjectName('brandName')
        names.addWidget(brand_name)
        self.description = W.QLabel()
        self.description.setObjectName('brandDetail')
        self.description.setWordWrap(True)
        names.addWidget(self.description)
        brand.addLayout(names, 1)
        side.addLayout(brand)
        side.addSpacing(22)
        self.nav = W.QListWidget()
        self.nav.setObjectName('nav')
        self.nav.setIconSize(QtCore.QSize(18, 18))
        self.nav.setFocusPolicy(QtCore.Qt.NoFocus)
        self.nav.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.nav_items={}
        for key,title,icon in NAVIGATION:
            if key=='drivers'and sys.platform=='darwin':title='USB 连接'
            item=W.QListWidgetItem(QtGui.QIcon(asset('nav/'+icon+'.svg')),title)
            item.setData(QtCore.Qt.UserRole,key);item.setSizeHint(QtCore.QSize(0,36))
            self.nav.addItem(item);self.nav_items[key]=item
        side.addWidget(self.nav, 1)
        base = W.QHBoxLayout()
        base.setContentsMargins(8, 10, 2, 0)
        caption = W.QLabel('原厂基础版本')
        caption.setObjectName('sidebarCaption')
        base.addWidget(caption)
        base.addStretch()
        self.firmware = W.QComboBox()
        self.firmware.addItems(['2.01'])
        base.addWidget(self.firmware)
        side.addLayout(base)
        layout.addWidget(sidebar)
        right = W.QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        layout.addLayout(right, 1)
        self.pages = W.QStackedWidget()
        right.addWidget(self.pages, 1)
        self.page_widgets={}
        builders=(('install',self.install_guide_page),('drivers',self.connection_page),
                  ('recovery',self.recovery_page),('looks',self.look_page),('sound',self.sound_page),
                  ('firmware',self.firmware_page),('trust',self.trust_page),('advanced',self.advanced_settings_page))
        for key,build in builders:
            build();self.page_widgets[key]=self.pages.widget(self.pages.count()-1)
        self.install_guide.bind()
        self.nav.currentItemChanged.connect(lambda item,previous:self.show_page(item.data(QtCore.Qt.UserRole))if item else None)
        self.description.setText('电脑端制作与编辑\nSSH / USB 更新 · ' + VERSION)
        self.select_page('install')
        self.polish_pages()
        footer = W.QFrame()
        footer.setObjectName('footer')
        activity = W.QVBoxLayout(footer)
        activity.setContentsMargins(0, 0, 0, 0)
        activity.setSpacing(0)
        self.progress = W.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        activity.addWidget(self.progress)
        bottom = W.QHBoxLayout()
        bottom.setContentsMargins(24, 9, 20, 10)
        bottom.setSpacing(8)
        self.status_dot = W.QLabel()
        self.status_dot.setObjectName('statusDot')
        bottom.addWidget(self.status_dot, 0, QtCore.Qt.AlignVCenter)
        bottom.addSpacing(2)
        self.status = W.QLabel('就绪。请按安装向导逐步操作；启动软件不会访问相机。')
        self.status.setObjectName('statusText')
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        bottom.addWidget(self.status, 1)
        self.log_toggle = W.QToolButton()
        self.log_toggle.setText('日志')
        self.log_toggle.setCheckable(True)
        self.log_toggle.setToolTip('显示或隐藏完整运行日志')
        bottom.addWidget(self.log_toggle)
        open_log = W.QPushButton('打开任务目录')
        open_log.clicked.connect(self.open_job)
        bottom.addWidget(open_log)
        export = W.QPushButton('导出诊断包')
        export.clicked.connect(self.export_logs)
        bottom.addWidget(export)
        self.stop = W.QPushButton('停止离线任务')
        self.stop.setEnabled(False)
        self.stop.clicked.connect(self.cancel_offline)
        bottom.addWidget(self.stop)
        activity.addLayout(bottom)
        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(150)
        self.log.setPlaceholderText('完整运行日志与原始报错会显示在这里。')
        self.log.setVisible(False)
        log_box = W.QHBoxLayout()
        log_box.setContentsMargins(20, 0, 20, 14)
        log_box.addWidget(self.log)
        activity.addLayout(log_box)
        self.log_toggle.toggled.connect(self.log.setVisible)
        right.addWidget(footer)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.poll_job)
        self.timer.start(250)

    def page(self, title, detail):
        wrapper = W.QScrollArea()
        wrapper.setWidgetResizable(True)
        wrapper.setFrameShape(W.QFrame.NoFrame)
        body = W.QWidget()
        body.setObjectName('pageBody')
        outer = W.QHBoxLayout(body)
        outer.setContentsMargins(44, 34, 36, 28)
        column = W.QWidget()
        column.setMaximumWidth(840)
        outer.addWidget(column, 1)
        outer.addStretch(0)
        layout = W.QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        label = W.QLabel(title)
        label.setProperty('pageTitle', True)
        layout.addWidget(label)
        hint = W.QLabel(detail)
        hint.setWordWrap(True)
        hint.setProperty('subtitle', True)
        layout.addWidget(hint)
        layout.addSpacing(8)
        wrapper.setWidget(body)
        self.pages.addWidget(wrapper)
        return layout

    def select_page(self,key):
        self.nav.setCurrentItem(self.nav_items[key])

    def show_page(self,key):
        self.install_guide.mount(key=='install')
        self.pages.setCurrentWidget(self.page_widgets[key])
        self.install_guide.refresh()

    def box(self, layout, title):
        group = W.QGroupBox(title)
        form = W.QFormLayout(group)
        form.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow)
        form.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
        layout.addWidget(group)
        return form

    def card(self, layout, title=None, *, stretch=0):
        """A grey tile with an optional heading; returns its vertical layout."""
        frame = W.QFrame()
        frame.setProperty('card', True)
        inner = W.QVBoxLayout(frame)
        inner.setContentsMargins(18, 16, 18, 16)
        inner.setSpacing(10)
        if title:
            heading = W.QLabel(title)
            heading.setProperty('section', True)
            inner.addWidget(heading)
        layout.addWidget(frame, stretch)
        return inner

    def advanced(self, layout, title):
        toggle = W.QToolButton()
        toggle.setText(title)
        toggle.setCheckable(True)
        toggle.setProperty('disclosure', True)
        toggle.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        toggle.setIcon(QtGui.QIcon(asset('chevron-right.svg')))
        toggle.setIconSize(QtCore.QSize(14, 14))
        content = W.QWidget()
        content.setVisible(False)
        inner = W.QVBoxLayout(content)
        inner.setContentsMargins(0, 0, 0, 6)
        inner.setSpacing(10)
        toggle.toggled.connect(content.setVisible)
        toggle.toggled.connect(lambda open: toggle.setIcon(QtGui.QIcon(asset('chevron-open.svg' if open else 'chevron-right.svg'))))
        layout.addSpacing(4)
        layout.addWidget(toggle, 0, QtCore.Qt.AlignLeft)
        layout.addWidget(content)
        return inner

    def polish_pages(self):
        """Apply the layout conventions every page shares.

        Long explanatory labels become secondary notes, and stand-alone
        buttons keep their natural width instead of stretching across the
        page. Widgets, names and behaviour are untouched.
        """
        from .lookeditor import LookEditor
        skip = tuple(self.pages.widget(i).findChildren(LookEditor) for i in range(self.pages.count()))
        editors = {editor for group in skip for editor in group}

        def inside_editor(widget):
            parent = widget
            while parent is not None:
                if parent in editors:return True
                parent = parent.parentWidget()
            return False

        for index in range(self.pages.count()):
            page = self.pages.widget(index)
            for label in page.findChildren(W.QLabel):
                standalone = isinstance(label.parentWidget().layout(), W.QVBoxLayout) and len(label.text()) >= 24
                if ((label.wordWrap() or standalone) and not inside_editor(label) and not any(
                        label.property(name) for name in ('hint','subtitle','pageTitle','callout','section','warning'))):
                    label.setProperty('note', True)
                    label.setWordWrap(True)
            column = page.widget().layout().itemAt(0).widget()
            self._align_buttons(column.layout(), editors)

    def _align_buttons(self, layout, editors):
        if layout is None or layout.property('fill'):return
        items = [layout.itemAt(i) for i in range(layout.count())]
        if isinstance(layout, W.QVBoxLayout):
            for item in items:
                widget = item.widget()
                if isinstance(widget, W.QPushButton):layout.setAlignment(widget, QtCore.Qt.AlignLeft)
        elif isinstance(layout, W.QHBoxLayout):
            widgets = [item.widget() for item in items if item.widget() is not None]
            if (widgets and not any(item.spacerItem() for item in items)
                    and all(isinstance(w, (W.QPushButton, W.QComboBox)) for w in widgets)):
                layout.addStretch(1)
        for item in items:
            if item.layout() is not None:
                self._align_buttons(item.layout(), editors)
            widget = item.widget()
            if widget is not None and widget not in editors and not isinstance(widget, W.QGroupBox) and widget.layout() is not None:
                self._align_buttons(widget.layout(), editors)

    def direct_args(self, group, **values):
        work = self.work(group)
        return dict(self.common(), workspace=work, **{key: value for key, value in values.items() if key != 'mode'})


    def install_guide_page(self):
        from .installguide import InstallGuide
        layout=self.page('安装向导',f'跟着下面的四步完成 {VERSION} 安装。已有驱动或已授信的相机，可以直接下一步。')
        layout.parentWidget().parentWidget().layout().setContentsMargins(28,22,28,20)
        self.install_guide=InstallGuide(self);layout.addWidget(self.install_guide,0,QtCore.Qt.AlignTop);layout.addStretch()


    def driver_step_failed(self,action):
        return action in ('usb_prepare','connect','driver_install')


    def show_reload_guide(self, *, mode=None):
        title='授信已写入，请继续刷前配置'if mode=='trust_install'else'读写已结束，请断电重开'
        W.QMessageBox.information(self, title, reloadguide.text(mode=mode))


    def field(self, form, key, label, *, kind=None, filter='All files (*)', value=''):
        line = W.QLineEdit(str(self.settings.get(key, value)))
        line.setObjectName(key)
        self.fields[key] = line
        if kind:
            row = W.QHBoxLayout()
            row.addWidget(line, 1)
            button = W.QPushButton('选择…')
            button.clicked.connect(lambda: self.browse(line, kind, filter))
            row.addWidget(button)
            form.addRow(label, row)
        else:
            form.addRow(label, line)
        return line

    def browse(self, field, kind, filter):
        if kind in ('folder','directory'):
            path = W.QFileDialog.getExistingDirectory(self, '选择目录', field.text())
        elif kind == 'save':
            path = W.QFileDialog.getSaveFileName(self, '保存文件', field.text(), filter)[0]
        else:
            path = W.QFileDialog.getOpenFileName(self, '选择文件', field.text(), filter)[0]
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
        layout = self.page('USB 连接' if sys.platform=='darwin' else '安装驱动与 USB 连接', '相机开机并选择“海量存储／Mass Storage”，使用可传数据的 USB 线。一次只连接一台相机。')
        form = self.box(layout, 'USB 连接')
        self.driver_identity = W.QComboBox()
        self.driver_identity.addItems(['普通连接 · 054C:0E8A', '服务连接 · 054C:0336'])
        form.addRow('连接身份' if sys.platform=='darwin' else '驱动目标', self.driver_identity)
        if sys.platform == 'darwin':
            self.field(form, 'mac_volume', 'macOS 相机存储卷', kind='folder', value='/Volumes/')
        self.button(layout, '检测相机' if sys.platform=='darwin' else '检测相机与驱动', 'driver_scan')
        if sys.platform == 'win32':
            # Manual Zadig installation sits beside the automatic one: many
            # computers where the automatic install fails succeed with it.
            drivers = W.QHBoxLayout()
            layout.addLayout(drivers)
            self.button(drivers, '准备两阶段驱动并测试连接（自动）', 'usb_prepare', primary=True)
            zadig = W.QPushButton('用 Zadig 手动安装驱动（自动失败时）')
            zadig.setObjectName('zadig_guide')
            zadig.setProperty('primary', True)
            zadig.clicked.connect(self.show_zadig_guide)
            drivers.addWidget(zadig)
            self.buttons.append(zadig)
        else:
            self.button(layout, '准备 USB 服务连接', 'usb_prepare', primary=True)
        self.button(layout, '单独安装所选身份的驱动（高级）' if sys.platform == 'win32'
                    else '检查 USB 访问（macOS 无需 Zadig）', 'driver_install',
                    lambda: {'pid': ['0e8a', '0336'][self.driver_identity.currentIndex()]})
        if sys.platform == 'darwin':
            self.button(layout, '推出选中的相机存储卷', 'mac_unmount', lambda: {'volume': self.text('mac_volume')})
        self.button(layout, '测试服务连接（不写固件）', 'connect')
        self.button(layout, '检测 USB 连接稳定性（只读）', 'usb_stability')
        if sys.platform == 'win32':
            self.button(layout, '卸载相机驱动，恢复 Windows 默认连接', 'driver_uninstall',
                        lambda: {'pids': ['0e8a', '0336']})
        hint = W.QLabel('连接中断后先查看完整日志。报错不会触发重新刷写或自动重装驱动。')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()

    def recovery_page(self):
        layout=self.page('一键恢复','先将版本设为 2.00，再手动卡刷原厂内容恢复包。')
        self.recovery_transport=self.transport_controls(layout,'recovery')
        self.recovery_transport.usb.setText('USB · 版本准备')
        self.recovery_usb_panel=W.QWidget();self.recovery_usb_panel.setObjectName('recoveryUsbPanel')
        usb=W.QVBoxLayout(self.recovery_usb_panel);usb.setContentsMargins(0,0,0,0);usb.setSpacing(10)
        self.recovery_usb_controls(usb);layout.addWidget(self.recovery_usb_panel)
        self.recovery_ssh_panel=W.QWidget();self.recovery_ssh_panel.setObjectName('recoverySshPanel')
        ssh=W.QVBoxLayout(self.recovery_ssh_panel);ssh.setContentsMargins(0,0,0,0);ssh.setSpacing(10)
        self.recovery_ssh_controls(ssh);layout.addWidget(self.recovery_ssh_panel)
        form=self.box(layout,'2. 生成原厂内容恢复包 · 电脑离线完成')
        self.field(form,'factory_voice_firmware','官方 2.01 BODYDATA.DAT',kind='file',filter='Sony firmware (*.DAT)')
        self.field(form,'factory_package_output','保存位置',value=self.work('factory-firmware'),kind='directory')
        self.button(layout,'生成原厂内容恢复包','firmware_factory_build',
            lambda:dict(sony_firmware=self.text('factory_voice_firmware'),workspace=self.text('factory_package_output'),automatic_identity=True),primary=True)
        download=W.QPushButton('打开索尼官方 2.01 固件下载页')
        from .screenreader import DOWNLOAD_URL
        download.clicked.connect(lambda:QtGui.QDesktopServices.openUrl(QtCore.QUrl(DOWNLOAD_URL)))
        layout.addWidget(download);self.buttons.append(download)
        note=W.QLabel('3. 版本准备完成并按提示重开后，将生成的 BODYDATA.DAT 放到 SD 卡根目录，'
            '在相机菜单手动更新。完成后检查菜单、拍摄与回放。\n'
            '恢复包保留官方 2.01 的机身程序、资源与包头版本，使用当前工具签名。'
            '单独修改版本号不会恢复原厂授信。')
        note.setWordWrap(True);layout.addWidget(note)
        layout.addStretch()
        self.recovery_transport.changed.connect(self.refresh_recovery_transport)
        self.refresh_recovery_transport();self.refresh_factory_controls()

    def refresh_recovery_transport(self):
        usb=self.recovery_transport.value()=='usb'
        self.recovery_usb_panel.setVisible(usb);self.recovery_ssh_panel.setVisible(not usb)

    def advanced_settings_page(self):
        layout=self.page('高级设置','连接设置、USB 版本修改与恢复授信。日常安装请使用“安装向导”。')
        self.connection_settings_controls(layout)
        self.advanced_trust_restore_button=self.trust_restore_control(layout)
        form=self.box(layout,'通过 USB 修改版本号')
        self.field(form,'usb_version_target','目标版本',value='2.00')
        self.button(layout,'通过 USB 修改版本号','usb_set_version',
            lambda:dict(self.common(),workspace=self.work('usb-version'),target_version=self.text('usb_version_target')))
        note=W.QLabel('只修改版本资料，不更换程序或功能。格式如 2.00、2.01、3.10。恢复官方 2.01 前请设为 2.00。')
        note.setWordWrap(True);layout.addWidget(note);layout.addStretch()

    def recovery_ssh_controls(self,layout):
        form=self.box(layout,'1. 将版本设为 2.00 · SSH')
        self.field(form,'factory_version_source','当前版本',value=VERSION)
        form.addRow('目标版本',W.QLabel('2.00'))
        self.button(layout,'通过 SSH 将版本设为 2.00','ssh_restore_version',
            lambda:dict(self.ssh_update_args(),workspace=self.work('version-restore'),source_version=self.text('factory_version_source')),primary=True)
        settings=W.QPushButton('SSH 连接设置…');settings.clicked.connect(lambda:self.select_page('advanced'))
        layout.addWidget(settings);self.buttons.append(settings)
        self.button(layout,'重开后核对本次 SSH 版本准备（可选）','ssh_verify_update',
            lambda:dict(self.ssh_update_args(),workspace=self.settings.get('factory_version_work','')))

    def recovery_usb_controls(self,layout):
        note=W.QLabel('1. 连接相机 USB 海量存储，将更新器版本资料设为 2.00。'
            '这一步仅修改两字节版本资料，机身程序由后续卡刷恢复。')
        note.setWordWrap(True);layout.addWidget(note)
        self.factory_button=W.QPushButton('通过 USB 将版本设为 2.00')
        self.factory_button.setObjectName('factoryPrimaryAction');self.factory_button.setProperty('primary',True)
        self.factory_button.clicked.connect(self.factory_action)
        layout.addWidget(self.factory_button);self.buttons.append(self.factory_button)
        self.factory_status=W.QLabel()
        self.factory_status.setWordWrap(True);layout.addWidget(self.factory_status)

    def factory_state(self):
        work=self.settings.get('factory_usb_version_work','')
        path=Path(work,'version-restore.private.json') if work else None
        try:state=json.loads(path.read_text(encoding='utf-8')) if path and path.is_file() else {}
        except (OSError,ValueError):state={}
        return state if isinstance(state,dict) else {}

    def factory_action(self):
        self.launch('usb_restore_version',dict(self.common(),workspace=self.work('card-recovery-version')))

    def refresh_factory_controls(self):
        state=self.factory_state()
        if state.get('phase')=='AWAITING_CARD_UPDATE':
            message='上次版本资料 2.00 已读回，USB 读写已结束；机身程序尚未恢复。请继续手动卡刷。'
        elif state.get('phase')=='NEEDS_REVIEW_NO_AUTOMATIC_REPLAY':
            message='上次版本准备停止，记录已保留；请先检查日志，不要重复未知写入。'
        else:
            message='完成版本准备后，按提示断电重开，再手动卡刷恢复包。'
        self.factory_status.setText(message)


    def firmware_args(self):
        from looktool import bundle
        use_custom=self.local_looks.isChecked() and self.local_custom_looks.isChecked()
        errors=self.firmware_look_editor.errors() if use_custom else []
        if errors:raise ValueError(' '.join(errors))
        custom=[{k:v for k,v in row.items() if k!='action'} for row in self.firmware_look_editor.values()] if use_custom else []
        if custom:bundle.documents(dict(looks=custom),allow_menu_icons=True)
        return dict(sony_firmware=self.text('firmware_source'),workspace=self.text('firmware_output'),
                    update_version=self.text('firmware_update_version'),
                    fl23=self.local_fl23.isChecked(),whitebalance=self.local_wb.isChecked(),
                    sound=self.local_sound.isChecked(),ssh=self.local_ssh.isChecked(),
                    custom_looks=self.local_looks.isChecked(),vertical=self.local_vertical.isChecked(),
                    precapture=False,voice_cleanup=True,
                    automatic_identity=True,
                    looks=custom,custom_sound=self.firmware_sound_args(),
                    preset_pack=presets.PACK if self.local_looks.isChecked() and self.local_presets.isChecked() else None)

    def firmware_sound_args(self):
        if not(self.local_sound.isChecked()and self.local_custom_sound.isChecked()):return None
        electronic=self.firmware_sound_electronic.isChecked()
        mechanical=self.firmware_sound_mechanical.isChecked()
        if not(electronic or mechanical):raise ValueError('请至少选择一种自定义快门声音的应用范围。')
        return dict(source=self.text('firmware_sound_source'),start=self.firmware_sound_start.value(),
                    duration=self.firmware_sound_duration.value(),
                    selection='both'if electronic and mechanical else'electronic'if electronic else'mechanical')

    def firmware_page(self):
        layout=self.page('本地修改官方固件',
            '选择固件保存位置，可直接选 SD 卡根目录。生成后继续首次授信和刷前配置，再手动卡刷。')
        form=self.box(layout,'来源与输出')
        self.field(form,'firmware_source','官方 A7C II 2.01 BODYDATA.DAT',kind='file',filter='Sony firmware (*.DAT);;All files (*)')
        self.field(form,'firmware_output','保存位置（可选 SD 卡）',value=self.work('local-firmware'),kind='directory')
        self.field(form,'firmware_update_version','更新头版本',value=VERSION).setText(VERSION)
        layout.setSizeConstraint(W.QLayout.SetMinimumSize)
        page_layout=layout
        layout=self.card(page_layout,'固件功能');layout.setSpacing(2)
        layout.setSizeConstraint(W.QLayout.SetMinimumSize)
        self.local_fl23=W.QCheckBox('加入 FL2／FL3');self.local_fl23.setChecked(True)
        self.local_wb=W.QCheckBox('加入自动白平衡优化');self.local_wb.setChecked(True)
        self.local_sound=W.QCheckBox('加入快门音效与自定义声音支持');self.local_sound.setChecked(True)
        self.local_looks=W.QCheckBox('应用自定义外观');self.local_looks.setChecked(True)
        self.local_vertical=W.QCheckBox('加入竖屏显示资源');self.local_vertical.setChecked(True)
        self.local_voice=W.QCheckBox('删除无障碍语音音频并禁用语音指南（必选，保留索引）')
        self.local_voice.setChecked(True);self.local_voice.setEnabled(False)
        self.local_ssh=W.QCheckBox('加入索尼云创内置接口');self.local_ssh.setChecked(True)
        self.local_ssh.setToolTip('需要先应用自定义外观。')
        layout.addWidget(self.local_looks)
        self.local_looks_panel=W.QFrame();self.local_looks_panel.setProperty('subpanel',True)
        looks=W.QVBoxLayout(self.local_looks_panel);looks.setContentsMargins(16,12,16,14);looks.setSpacing(10)
        choices=W.QHBoxLayout();choices.setSpacing(22)
        self.local_presets=W.QRadioButton('使用默认六款')
        self.local_custom_looks=W.QRadioButton('自选外观')
        self.local_look_choices=W.QButtonGroup(self.local_looks_panel)
        for index,button in enumerate((self.local_presets,self.local_custom_looks)):
            self.local_look_choices.addButton(button,index);choices.addWidget(button)
        self.local_presets.setChecked(True);choices.addStretch();looks.addLayout(choices)
        self.local_default_looks=W.QWidget();default_box=W.QVBoxLayout(self.local_default_looks)
        default_box.setContentsMargins(0,0,0,0);default_box.setSpacing(6)
        self.local_preset_summary=W.QLabel('默认包含以下六款，依次应用到槽位 1–6：')
        self.local_preset_summary.setProperty('note',True);default_box.addWidget(self.local_preset_summary)
        names=W.QGridLayout();names.setHorizontalSpacing(20);names.setVerticalSpacing(5)
        for index,name in enumerate(presets.NAMES):
            label=W.QLabel('%d · %s'%(index+1,name));label.setWordWrap(True)
            label.setObjectName('firmwareDefaultLookName%d'%(index+1))
            names.addWidget(label,index//2,index%2)
        names.setColumnStretch(0,1);names.setColumnStretch(1,1);default_box.addLayout(names)
        looks.addWidget(self.local_default_looks)
        self.local_custom_looks_panel=W.QWidget();custom_box=W.QVBoxLayout(self.local_custom_looks_panel)
        custom_box.setContentsMargins(0,0,0,0);custom_box.setSpacing(8)
        from .lookeditor import LookEditor
        self.firmware_look_editor=LookEditor(write_only=True,for_firmware=True);custom_box.addWidget(self.firmware_look_editor)
        custom_note=W.QLabel('外观文件中附带的菜单图标会一同加入固件；未选择的槽位使用原生 ST。')
        custom_note.setWordWrap(True);custom_note.setProperty('note',True);custom_box.addWidget(custom_note)
        looks.addWidget(self.local_custom_looks_panel)
        panel_row=W.QHBoxLayout();panel_row.setContentsMargins(48,4,0,8);panel_row.addWidget(self.local_looks_panel)
        layout.addLayout(panel_row)
        def refresh_looks():
            on=self.local_looks.isChecked()
            self.local_looks_panel.setVisible(on);self.local_looks_panel.setEnabled(on)
            self.local_default_looks.setVisible(on and self.local_presets.isChecked())
            self.local_custom_looks_panel.setVisible(on and self.local_custom_looks.isChecked())
        def custom_changed(checked):
            self.local_ssh.setEnabled(checked)
            if not checked:self.local_ssh.setChecked(False)
            refresh_looks()
        self.local_looks.toggled.connect(custom_changed)
        self.local_look_choices.idToggled.connect(lambda _index,_checked:refresh_looks())
        refresh_looks()
        for item in (self.local_voice,self.local_fl23,self.local_wb,self.local_sound):layout.addWidget(item)
        sound_layout=layout
        self.local_sound_panel=W.QFrame();self.local_sound_panel.setProperty('subpanel',True)
        sounds=W.QVBoxLayout(self.local_sound_panel);sounds.setContentsMargins(16,12,16,14);sounds.setSpacing(10)
        sounds.setSizeConstraint(W.QLayout.SetMinimumSize)
        choices=W.QHBoxLayout();choices.setSpacing(22)
        self.local_default_sound=W.QRadioButton('使用默认声音')
        self.local_custom_sound=W.QRadioButton('自定义声音')
        self.local_sound_choices=W.QButtonGroup(self.local_sound_panel)
        for index,button in enumerate((self.local_default_sound,self.local_custom_sound)):
            self.local_sound_choices.addButton(button,index);choices.addWidget(button)
        self.local_default_sound.setChecked(True);choices.addStretch();sounds.addLayout(choices)
        self.firmware_default_sound=W.QLabel('使用内置默认快门声音。')
        self.firmware_default_sound.setProperty('note',True);sounds.addWidget(self.firmware_default_sound)
        self.firmware_sound_panel=W.QWidget();sound_form=W.QFormLayout(self.firmware_sound_panel)
        sound_form.setContentsMargins(0,0,0,0);sound_form.setHorizontalSpacing(18);sound_form.setVerticalSpacing(10)
        sound_form.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow)
        sound_form.setSizeConstraint(W.QLayout.SetMinimumSize)
        self.field(sound_form,'firmware_sound_source','声音文件',kind='file',
            filter='Audio / video (*.wav *.mp3 *.mp4 *.m4a *.flac *.ogg);;All files (*)')
        sound_form.itemAt(0,W.QFormLayout.FieldRole).layout().setSpacing(10)
        self.firmware_sound_start=W.QDoubleSpinBox();self.firmware_sound_start.setRange(0,86400)
        self.firmware_sound_start.setDecimals(3)
        self.firmware_sound_duration=W.QDoubleSpinBox();self.firmware_sound_duration.setRange(.01,2)
        self.firmware_sound_duration.setDecimals(3);self.firmware_sound_duration.setValue(.08)
        timing=W.QHBoxLayout();timing.setSpacing(10);timing.addWidget(W.QLabel('起点'))
        timing.addWidget(self.firmware_sound_start);timing.addSpacing(14);timing.addWidget(W.QLabel('长度'))
        timing.addWidget(self.firmware_sound_duration);timing.addStretch()
        sound_form.addRow('片段（秒）',timing)
        targets=W.QHBoxLayout();targets.setSpacing(24)
        self.firmware_sound_electronic=W.QCheckBox('电子快门');self.firmware_sound_electronic.setChecked(True)
        self.firmware_sound_mechanical=W.QCheckBox('机械快门')
        targets.addWidget(self.firmware_sound_electronic);targets.addWidget(self.firmware_sound_mechanical);targets.addStretch()
        sound_form.addRow('应用范围',targets)
        sound_note=W.QLabel('生成时自动转换所选片段，随固件一起写入。');sound_note.setWordWrap(True)
        sound_form.addRow(sound_note)
        sounds.addWidget(self.firmware_sound_panel)
        panel_row=W.QHBoxLayout();panel_row.setContentsMargins(48,4,0,8);panel_row.addWidget(self.local_sound_panel)
        sound_layout.addLayout(panel_row)
        def refresh_sound():
            enabled=self.local_sound.isChecked()
            self.local_sound_panel.setVisible(enabled)
            self.firmware_default_sound.setVisible(enabled and self.local_default_sound.isChecked())
            self.firmware_sound_panel.setVisible(enabled and self.local_custom_sound.isChecked())
        self.local_sound.toggled.connect(refresh_sound)
        self.local_sound_choices.idToggled.connect(lambda _index,_checked:refresh_sound());refresh_sound()
        for item in (self.local_vertical,self.local_ssh):sound_layout.addWidget(item)
        layout=page_layout
        self.firmware_config_notice=W.QLabel(reloadguide.PREFLASH_SETTINGS+
            '已授信的机身只需写配置；卡刷包沿用原厂设置迁移，不在更新末尾执行额外配置脚本。'
            '竖屏显示通过刷前配置启用，不增加机内开关菜单。')
        self.firmware_config_notice.setWordWrap(True);layout.addWidget(self.firmware_config_notice)
        layout.addSpacing(6)
        self.button(layout,'生成本地固件候选（不访问相机）','firmware_build',self.firmware_args,primary=True)
        layout.addStretch()

    def trust_page(self):
        layout=self.page('首次授信','先准备固件和 SD 卡，最后通过 USB 写入配置，随后直接手动卡刷。已授信的机身无需重复安装公钥，可以只写配置。')
        note=W.QLabel('第一次使用时安装机身公钥，软件会自动保留原始备份。已授信的相机可以直接写入刷前配置。')
        note.setWordWrap(True);layout.addWidget(note)
        self.trust_install_button=self.button(layout,'通过 USB 安装机身公钥','firmware_trust_install',
            lambda:dict(workspace=self.work('trust-install')),primary=True)
        self.trust_restore_button=self.trust_restore_control(layout)
        self.config_group=W.QGroupBox('刷前写入配置');config=W.QVBoxLayout(self.config_group)
        self.config_fl23=W.QCheckBox('启用 FL2／FL3')
        self.config_vertical=W.QCheckBox('启用竖屏显示（不增加机内开关菜单）')
        self.config_voice=W.QCheckBox('关闭语音指南及快捷触发')
        for widget in (self.config_fl23,self.config_vertical,self.config_voice):
            widget.setChecked(True);config.addWidget(widget)
            widget.toggled.connect(self.refresh_trust_controls)
        self.config_voice.setEnabled(False)
        for local,config_box in ((self.local_fl23,self.config_fl23),(self.local_vertical,self.config_vertical)):
            local.toggled.connect(config_box.setChecked)
            config_box.toggled.connect(local.setChecked)
        config_note=W.QLabel('勾选项应与“生成固件”页一致；只写入并保存所选设置，不刷写程序。'
            f'支持在官方 2.01 或现有 3.10／{VERSION} 上刷前准备。'+reloadguide.PREFLASH_SETTINGS)
        config_note.setWordWrap(True);config.addWidget(config_note)
        self.config_install_button=self.button(config,'通过 USB 写入所选功能配置','firmware_settings_install',
            self.feature_settings_args,primary=True)
        layout.addWidget(self.config_group)
        self.trust_state=W.QLabel();self.trust_state.setWordWrap(True);layout.addWidget(self.trust_state)
        self.refresh_trust_controls();layout.addStretch()

    def trust_verify_source(self):
        return self.settings.get('trust_latest_work')or self.settings.get('trust_install_work','')

    def trust_restore_control(self,layout):
        button=W.QPushButton('恢复授信（恢复原厂公钥）')
        button.clicked.connect(self.restore_trust)
        layout.addWidget(button);self.buttons.append(button)
        return button

    def restore_trust(self):
        if self.process is not None:return
        from .trustinstall import STATE
        source=self.settings.get('trust_install_work','')
        if not source or not (Path(source)/STATE).is_file():
            path,_=W.QFileDialog.getOpenFileName(self,'选择首次授信记录',source,
                '首次授信记录 ('+STATE+')')
            if not path:return
            source=str(Path(path).parent)
        self.launch('firmware_trust_restore',dict(workspace=self.work('trust-restore'),source_workspace=source))

    def remember_trust_install(self,result):
        from .trustinstall import STATE
        previous=self.settings.get('trust_install_work','')
        try:
            state=json.loads((Path(previous)/STATE).read_text(encoding='utf-8')) if previous else {}
        except (OSError,ValueError):state={}
        if not state.get('backup_verified') or state.get('identity')!=result.get('identity'):
            self.settings['trust_install_work']=result['workspace']

    def feature_settings_args(self):
        return dict(workspace=self.work('preflash-settings'),fl23=self.config_fl23.isChecked(),
            vertical=self.config_vertical.isChecked(),voice_cleanup=self.config_voice.isChecked())

    def refresh_trust_controls(self):
        original=self.settings.get('trust_install_work','');origin=Path(original)
        try:
            from .trustinstall import STATE
            state=json.loads((origin/STATE).read_text(encoding='utf-8')) if original else {}
            restorable=state.get('mode')=='trust_install' and state.get('backup_verified',False)
            latest=json.loads((Path(self.trust_verify_source())/STATE).read_text(encoding='utf-8')) if self.trust_verify_source() else {}
        except (OSError,ValueError):state={};latest={};restorable=False
        idle=self.process is None
        self.config_install_button.setEnabled(idle and any(widget.isChecked() for widget in
            (self.config_fl23,self.config_vertical,self.config_voice)))
        restored=latest.get('mode')=='trust_restore' and latest.get('phase')in ('AWAITING_RELOAD','LOADED')
        phase=latest.get('phase',state.get('phase'))
        unknown=latest.get('write_attempted',state.get('write_attempted',False)) and phase not in ('AWAITING_RELOAD','LOADED')
        self.trust_install_button.setEnabled(idle and not unknown)
        self.trust_restore_button.setEnabled(idle)
        if hasattr(self,'advanced_trust_restore_button'):self.advanced_trust_restore_button.setEnabled(idle)
        self.trust_state.setText('上次授信尚未确认完成，请查看日志，不要重复安装。' if unknown else
            '上次操作是恢复原厂授信，安装本工具生成的固件前需要重新授信。' if restored else
            '已保留授信记录；需要时可再次安装公钥。恢复授信会恢复原厂公钥。' if restorable else '')
        if hasattr(self,'install_guide'):self.install_guide.refresh()


    def ssh_update_args(self,**values):
        baseline=self.settings.get('ssh_update_baseline','')
        public=Path(baseline).parent/'ssh/host-public.json' if baseline else None
        args=dict(self.common(),workspace=self.work('ssh-update'),
                    host_public=str(public) if public and public.is_file() else None,bind_ip=self.text('ssh_update_ip'),
                    client_private=None,previous_look_update=self.settings.get('look_ssh_work'))
        args.update(values)
        return args


    def connection_settings_controls(self,layout):
        form=self.box(layout,'SSH · Wi-Fi 连接')
        self.field(form,'ssh_update_ip','相机 Wi-Fi IPv4')
        form.addRow('登录信息',W.QLabel('root / A7C2Tools · 端口 2222（自动登录）'))
        self.button(layout,'测试 SSH 连接','ssh_connect',self.ssh_update_args,primary=True)
        note=W.QLabel('相机固件需包含索尼云创内置接口。开启相机 Wi-Fi 后连接；关闭 Wi-Fi 后服务自动停止。')
        note.setWordWrap(True);layout.addWidget(note)
        usb=self.box(layout,'USB · 线刷连接')
        usb.addRow(W.QLabel('相机开机，USB 连接模式选择“海量存储”。'))
        row=W.QHBoxLayout();usb.addRow(row)
        self.button(row,'检测相机与驱动','driver_scan')
        driver=W.QPushButton('USB 连接工具…' if sys.platform=='darwin' else 'USB 驱动安装与连接工具…')
        driver.clicked.connect(lambda:self.select_page('drivers'));row.addWidget(driver);self.buttons.append(driver)

    def transport_controls(self,layout,key):
        row=W.QHBoxLayout();row.addWidget(W.QLabel('连接方式'))
        choice=TransportChoice(key)
        row.addWidget(choice);row.addStretch()
        settings=W.QPushButton('连接设置…');settings.clicked.connect(lambda:self.select_page('advanced'))
        row.addWidget(settings);self.buttons.append(settings);layout.addLayout(row)
        return choice


    def look_page(self):
        from .lookeditor import LookEditor
        layout=self.page('滤镜','选择槽位、名称和 A7Look 文件，批量应用；DCP／LUT 转换在电脑完成。')
        self.look_transport=self.transport_controls(layout,'look')
        self.look_pending=W.QLabel();self.look_pending.setWordWrap(True);self.look_pending.setProperty('callout',True);layout.addWidget(self.look_pending)
        self.look_editor=LookEditor();layout.addWidget(self.look_editor)
        self.look_button=W.QPushButton('添加操作项后继续');self.look_button.setProperty('primary',True)
        self.look_button.setObjectName('action_direct_looks_import');self.look_button.clicked.connect(self.launch_look_changes)
        layout.addWidget(self.look_button);self.buttons.append(self.look_button)
        tools=W.QHBoxLayout();layout.addLayout(tools)
        library_title='打开内置六款 A7Look' if sys.platform=='win32' else '打开内置 DCP／A7Look 配对库'
        for title,callback in [(library_title,self.open_profile_library),('从 DCP／LUT 生成 A7Look＋DCP…',self.compiler_dialog),('安装 LrC 自动识别插件…',self.plugin_dialog)]:
            button=W.QPushButton(title);button.clicked.connect(callback);tools.addWidget(button);self.buttons.append(button)
        formats=W.QPushButton('LUT 格式说明：ST / sRGB，不是 S-Log3…')
        formats.clicked.connect(self.show_look_format_guide);layout.addWidget(formats);self.buttons.append(formats)
        layout.addWidget(W.QLabel('写入页选择 .a7look；.cube / .dcp 先用上方工具转换。仅更改清单内的槽位。'))
        self.look_help=W.QLabel();self.look_help.setWordWrap(True);layout.addWidget(self.look_help)
        self.look_verify_button=self.button(layout,'SSH · 重开后核对上次滤镜更新','ssh_verify_update',
                    lambda:dict(self.ssh_update_args(),workspace=self.settings.get('look_ssh_work','')))
        layout.addStretch()
        self._look_displayed_pending=None;self._look_refreshing=False
        self.look_editor.changed.connect(self.refresh_look_controls)
        self.look_transport.changed.connect(self.refresh_look_controls)
        self.refresh_look_controls()

    def open_profile_library(self):
        from .profilelibrary import location
        folder=location()
        if not (folder/'catalog.json').is_file():
            W.QMessageBox.warning(self,'外观库缺失','没有找到内置外观库，请保留完整工具包目录。\n查找位置：'+str(folder));return
        if not QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(folder))):
            W.QMessageBox.warning(self,'无法打开配对库','系统未能打开配对库文件夹。位置：\n'+str(folder))

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
                    return prior,dict(phase='BACKGROUND_UNCONFIRMED',error='后台任务尚未确认结束，请等待原结果或查看日志，不重复写入。')
            if Path(prior,'command.private.json').is_file():return None
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
            self.look_transport.setEnabled(not busy and not pending)
            if pending:self.look_transport.select('usb')
            ssh=self.look_transport.value()=='ssh'
            self.look_verify_button.setVisible(ssh)
            self.look_help.setText('连接相机热点后直接应用；能力和状态自动读取，不需要旧构建记录。完成后按提示断电加载。' if ssh else
                '同一次操作自动检查当前状态、写入并完整读回。结束后按弹窗断电加载，无需单独点击核对。')
            if not pending and self.look_transport.value()=='ssh':
                rows=self.look_editor.values();busy=self.process is not None
                self.look_pending.hide();self.look_editor.setEnabled(not busy)
                self.look_button.setText('通过 SSH 应用这 %d 项更改'%len(rows) if rows else '添加操作项后继续')
                self.look_button.setEnabled(bool(rows) and not self.look_editor.errors() and not busy)
                return
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
                    text='上次操作正在等待资源续接，将沿用已保存的清单。'
                    self.look_button.setText('继续槽位更改')
                else:
                    from .lookbatch import read_only_failure
                    if read_only_failure(state):
                        text='上次在写入前停止，旧记录已保留；可以调整清单后重试。'
                        self.look_editor.setEnabled(not busy)
                        self.look_button.setText('重试本次更改（上次未写入）')
                        self.look_button.setEnabled(not busy and bool(self.look_editor.values()) and not self.look_editor.errors())
                    else:
                        text='上次操作尚未完成；请查看原任务记录，不自动重复写入。'
                        self.look_button.setText('查看未完成任务记录')
                self.look_pending.setText(text);self.look_pending.show()
            else:
                if self._look_displayed_pending is not None:
                    self._look_displayed_pending=None;self.look_editor.set_operations([])
                self.look_pending.hide();self.look_editor.setEnabled(not busy)
                rows=self.look_editor.values()
                self.look_button.setText('查看并应用这 %d 项更改'%len(rows) if rows else '添加操作项后继续')
                self.look_button.setEnabled(bool(rows) and not self.look_editor.errors() and not busy)
        finally:self._look_refreshing=False

    def look_batch_args(self):
        return self.direct_args('look',operations=self.look_editor.values())

    def launch_look_changes(self):
        if not self.look_pending_state() and self.look_transport.value()=='ssh':
            self.launch('ssh_save_looks',dict(self.ssh_update_args(),workspace=self.work('ssh-look'),operations=self.look_editor.values()))
            return
        pending=self.look_pending_state()
        if pending:
            prior,state=pending;phase=state.get('phase')
            if phase in ('AWAITING_RESOURCE_RELOAD','RESOURCE_RELOAD_VERIFIED') or (phase=='NEEDS_REVIEW' and state.get('forward_name_build',{}).get('stream_install') and 'readonly=-16' in state.get('error','')):
                self.launch('direct_resume_looks',dict(self.common(),workspace=self.work('look'),failed_workspace=prior));return
            from .lookbatch import read_only_failure
            if read_only_failure(state):
                self.launch('direct_looks_import',self.look_batch_args());return
            W.QMessageBox.warning(self,'上次任务尚未完成',state.get('error','请保留原记录，核对未知结果后再继续。')+'\n任务目录：'+prior)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(prior));return
        self.launch('direct_looks_import',self.look_batch_args())


    def sound_page(self):
        layout = self.page('快门音效', '在电脑导入、试听和调整音量，再通过 SSH 或 USB 应用到相机。')
        self.sound_transport=self.transport_controls(layout,'sound')
        outer=layout;columns=W.QHBoxLayout();columns.setSpacing(14);outer.addLayout(columns)
        prepare=self.card(columns,'1 · 在电脑准备声音',stretch=1);apply=self.card(columns,'2 · 应用自定义声音',stretch=1)
        for column in (prepare,apply):column.setProperty('fill',True);column.setSpacing(12)
        layout=prepare
        args = lambda: dict(self.common(), workspace=self.text('sound_work'), backup=self.text('sound_backup'))
        media = W.QFormLayout();media.setHorizontalSpacing(14);media.setVerticalSpacing(10)
        media.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow);layout.addLayout(media)
        self.field(media, 'sound_source', '声音文件', kind='file', filter='Audio / video (*.wav *.mp3 *.mp4 *.m4a *.flac *.ogg);;All files (*)')
        media.itemAt(0,W.QFormLayout.FieldRole).layout().setSpacing(10)
        self.sound_start = W.QDoubleSpinBox()
        self.sound_start.setRange(0, 86400)
        self.sound_start.setDecimals(3)
        self.sound_duration = W.QDoubleSpinBox()
        self.sound_duration.setRange(.01, 2)
        self.sound_duration.setDecimals(3)
        self.sound_duration.setValue(.08)
        timing=W.QHBoxLayout();timing.setSpacing(10);timing.addWidget(W.QLabel('起点'));timing.addWidget(self.sound_start)
        timing.addSpacing(14);timing.addWidget(W.QLabel('长度'));timing.addWidget(self.sound_duration)
        media.addRow('片段（秒）',timing)
        row = W.QHBoxLayout();row.setSpacing(12)
        layout.addLayout(row)
        self.button(row, '导入并转换所选片段', 'sound_import', lambda: dict(args(), source=self.text('sound_source'),
            start=self.sound_start.value(), duration=self.sound_duration.value(), peak=.4))
        volume = W.QHBoxLayout();volume.setSpacing(12)
        layout.addLayout(volume)
        self.button(volume, '音量降低 −3 dB', 'sound_volume', lambda: dict(args(), decibels=-3))
        self.button(volume, '音量提高 +3 dB', 'sound_volume', lambda: dict(args(), decibels=3))
        self.button(layout, '还原转换时音量', 'sound_volume', lambda: dict(args(), reset=True))
        preview=W.QHBoxLayout();preview.setSpacing(12);layout.addLayout(preview)
        play=W.QPushButton('在电脑试听');play.clicked.connect(self.preview_sound)
        preview.addWidget(play);self.buttons.append(play)
        stop=W.QPushButton('停止试听');stop.clicked.connect(self.stop_sound_preview)
        preview.addWidget(stop);self.buttons.append(stop)
        self.sound_preview_status=W.QLabel('导入后可试听；音量调整只在电脑完成。')
        self.sound_preview_status.setWordWrap(True);layout.addWidget(self.sound_preview_status)
        prepare.addStretch();layout=apply
        targets=W.QVBoxLayout();targets.setSpacing(8)
        self.sound_electronic=W.QCheckBox('应用于电子快门声音');self.sound_electronic.setChecked(True)
        self.sound_mechanical=W.QCheckBox('应用于机械快门声音')
        targets.addWidget(self.sound_electronic);targets.addWidget(self.sound_mechanical);layout.addLayout(targets)
        save=W.QPushButton('保存到所选快门');save.setObjectName('saveSelectedSound');save.setProperty('primary',True)
        save.clicked.connect(self.save_sound);layout.addWidget(save);self.buttons.append(save)
        hint=W.QLabel('两项都勾选即可同时应用。保存使用当前调整后的声音，并开启所选音效；完成后按提示断电重开。')
        hint.setWordWrap(True);layout.addWidget(hint)
        layout.addSpacing(6)
        heading=W.QLabel('独立开关 · 保留已保存的声音');heading.setProperty('section',True);layout.addWidget(heading)
        switches=W.QFormLayout();switches.setHorizontalSpacing(14);switches.setVerticalSpacing(8)
        switches.setFieldGrowthPolicy(W.QFormLayout.AllNonFixedFieldsGrow);layout.addLayout(switches)
        for selection,label in (('electronic','电子'),('mechanical','机械')):
            row=W.QHBoxLayout();row.setSpacing(12)
            for enabled,title in ((True,'开启'),(False,'关闭')):
                button=W.QPushButton(title)
                button.setObjectName('switch_'+selection+'_'+('on' if enabled else 'off'))
                button.setToolTip(title+label+'快门音效')
                button.clicked.connect(lambda checked=False,selection=selection,enabled=enabled:self.switch_sound(selection,enabled))
                row.addWidget(button);self.buttons.append(button)
            switches.addRow(label+'快门',row)
        note=W.QLabel('机械快门的开关仅控制扬声器音效，机械结构本身仍会发声。')
        note.setWordWrap(True);layout.addWidget(note)
        apply.addStretch();layout=outer
        optional=self.advanced(layout,'USB 高级工具')
        optional.parentWidget().setObjectName('soundUsbTools')
        # Keep existing workspace paths internally; no manual record controls.
        for key,default in (('sound_work',data_root()/'sound'),('sound_backup',data_root()/'sound-backup')):
            field=W.QLineEdit(str(self.settings.get(key,default)),self)
            field.setObjectName(key);field.hide();self.fields[key]=field
        self.button(optional,'USB · 相机内临时试听','sound_audition',args)
        self.button(optional, 'USB · 恢复原厂快门声音', 'sound_restore_sound', args)
        layout.addStretch()

    def sound_selection(self):
        electronic,mechanical=self.sound_electronic.isChecked(),self.sound_mechanical.isChecked()
        if not (electronic or mechanical):raise ValueError('请至少勾选一种快门声音。')
        return 'both' if electronic and mechanical else 'electronic' if electronic else 'mechanical'

    def save_sound(self):
        try:selection=self.sound_selection()
        except ValueError as exc:
            W.QMessageBox.information(self,'选择应用范围',str(exc));return
        if self.sound_transport.value()=='ssh':
            self.launch('ssh_sound_custom',dict(self.ssh_update_args(),workspace=self.work('ssh-sound'),
                sound_workspace=self.text('sound_work'),selection=selection))
        else:
            self.launch('sound_install',dict(self.common(),workspace=self.text('sound_work'),
                backup=self.text('sound_backup'),sound_target=selection))

    def switch_sound(self,selection,enabled):
        if self.sound_transport.value()=='ssh':
            self.launch('ssh_sound_switch',dict(self.ssh_update_args(),workspace=self.work('ssh-sound'),selection=selection,enabled=enabled))
        else:
            action=('sound_mechanical_' if selection=='mechanical' else 'sound_')+('on' if enabled else 'off')
            self.launch(action,dict(self.common(),workspace=self.text('sound_work')))


    def stop_sound_preview(self):
        if hasattr(self,'sound_player'):self.sound_player.stop()

    def preview_sound(self):
        from .actions.sound import converted_file
        try:path=converted_file(self.text('sound_work'),'preview.private.wav')
        except (ValueError,OSError,KeyError) as exc:
            W.QMessageBox.information(self,'请先准备声音',str(exc));return
        from PySide6.QtMultimedia import QAudioOutput,QMediaPlayer
        if not hasattr(self,'sound_player'):
            self.sound_player=QMediaPlayer(self);self.sound_output=QAudioOutput(self)
            self.sound_output.setVolume(1);self.sound_player.setAudioOutput(self.sound_output)
            self.sound_player.errorOccurred.connect(lambda *args:self.sound_preview_status.setText('电脑试听失败：'+self.sound_player.errorString()))
        self.sound_player.stop();self.sound_player.setSource(QtCore.QUrl.fromLocalFile(str(path)))
        self.sound_player.play();self.sound_preview_status.setText('正在电脑播放当前声音。')


    def show_zadig_guide(self):
        from .zadigguide import TITLE, TEXT, URL
        dialog = W.QDialog(self); dialog.setWindowTitle(TITLE); dialog.resize(820, 680)
        layout = W.QVBoxLayout(dialog)
        content = W.QTextBrowser(); content.setPlainText(TEXT); layout.addWidget(content)
        row = W.QHBoxLayout(); layout.addLayout(row)
        download = W.QPushButton('打开 Zadig 下载页'); download.setProperty('primary', True)
        download.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(URL)))
        close = W.QPushButton('关闭'); close.clicked.connect(dialog.accept)
        row.addWidget(download); row.addWidget(close)
        dialog.exec()

    def show_look_format_guide(self):
        from .lookguide import TITLE,TEXT
        dialog=W.QDialog(self);dialog.setWindowTitle(TITLE);dialog.resize(800,650)
        layout=W.QVBoxLayout(dialog)
        content=W.QTextBrowser();content.setPlainText(TEXT);layout.addWidget(content)
        close=W.QPushButton('关闭');close.clicked.connect(dialog.accept);layout.addWidget(close)
        dialog.exec()

    def compiler_dialog(self):
        dialog = W.QDialog(self)
        dialog.setWindowTitle('生成 A7Look ＋ DCP')
        dialog.resize(820, 760)
        layout = W.QVBoxLayout(dialog)
        hint = W.QLabel('同时输出同名 A7Look 和 DCP。CUBE 可选择输入曲线／色域与输出编码，支持常用 Log、宽色域及 PQ／HLG；DCP 保留原参考颜色。\n文件名识别仅为建议，请按 LUT 作者说明确认。M4 兼容项使用近似表；最终用于 SDR 照片外观，不会开启相机视频 Log。只生成文件，不写相机。')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        help_button=W.QPushButton('支持哪些格式和色彩空间？查看完整说明…')
        help_button.clicked.connect(self.show_look_format_guide);layout.addWidget(help_button)
        form = self.box(layout, '源文件与输出')
        self.field(form, 'compile_source', 'DCP / CUBE', kind='file', filter='Reference (*.dcp *.cube)')
        self.field(form, 'compile_name', '外观名称')
        from looktool import lutspaces
        spaces=lutspaces.options()
        input_space=W.QComboBox();output_space=W.QComboBox()
        for row in spaces['inputs']:input_space.addItem(row['label'],row['key'])
        input_space.addItem('自备 ST → LUT 输入的 bridge CUBE','custom')
        for row in spaces['outputs']:output_space.addItem(row['label'],row['key'])
        form.addRow('CUBE 输入空间',input_space);form.addRow('CUBE 输出空间',output_space)
        self.field(form,'compile_input_bridge','自备 bridge（高级）',kind='file',filter='CUBE (*.cube)')
        self.fields['compile_input_bridge'].setEnabled(False)
        input_space.currentIndexChanged.connect(lambda *_:self.fields['compile_input_bridge'].setEnabled(input_space.currentData()=='custom'))
        identify=W.QPushButton('从文件名／TITLE 读取建议（仍需确认）')
        def suggest_space():
            try:
                suggestion=lutspaces.suggest(Path(self.text('compile_source')))
                index=input_space.findData(suggestion['input_space'])
                if index>=0:input_space.setCurrentIndex(index)
                index=output_space.findData(suggestion['output_space'])
                if index>=0:output_space.setCurrentIndex(index)
            except (OSError,ValueError)as error:W.QMessageBox.information(dialog,'未读取到建议',str(error))
        identify.clicked.connect(suggest_space);form.addRow('',identify)
        self.field(form, 'compile_icon', '菜单图标（可选）')
        self.fields['compile_icon'].setMaxLength(4)
        self.fields['compile_icon'].setPlaceholderText('自动匹配，或输入 1–4 字符，如 F400、5213、RN')
        include_icon=W.QCheckBox('附带图标（用于机内 API／SSH／生成固件）')
        include_icon.setChecked(True);form.addRow('',include_icon)
        include_icon.toggled.connect(self.fields['compile_icon'].setEnabled)
        compatibility=W.QLabel('名称使用完整名称；已知外观自动匹配图案。USB 直接导入请取消“附带图标”。')
        compatibility.setWordWrap(True);form.addRow('',compatibility)
        from looktool.looklabels import lookup
        preview=W.QLabel();preview.setMinimumHeight(82);preview.setAlignment(QtCore.Qt.AlignCenter)
        form.addRow('图标预览',preview)
        def update_icon_preview(*_):
            if not include_icon.isChecked():preview.clear();preview.setText('仅生成完整名称和色彩数据');return
            text=self.text('compile_icon')
            if not text:preview.clear();preview.setText('可输入自定义图标缩写');return
            from looktool import iconfile
            try:pixels=iconfile.mask(iconfile.from_text(text))
            except (ValueError,OSError) as error:preview.clear();preview.setText(str(error));return
            image=QtGui.QImage(pixels,26,19,26,QtGui.QImage.Format_Grayscale8).copy()
            preview.setPixmap(QtGui.QPixmap.fromImage(image).scaled(104,76,QtCore.Qt.KeepAspectRatio,QtCore.Qt.FastTransformation))
        include_icon.toggled.connect(update_icon_preview)
        self.fields['compile_icon'].textChanged.connect(update_icon_preview)
        last_auto=dict(name='',icon='')
        def suggest_icon(*_):
            row=lookup(self.text('compile_name'));text=row['icon_text'] if row else 'LUT'
            if self.text('compile_icon') in ('',last_auto['icon']):self.fields['compile_icon'].setText(text)
            last_auto['icon']=text
        def suggest_name(*_):
            row=lookup(self.text('compile_source'))
            if row and self.text('compile_name') in ('',last_auto['name']):self.fields['compile_name'].setText(row['name'])
            last_auto['name']=row['name'] if row else ''
            suggest_icon()
        self.fields['compile_source'].textChanged.connect(suggest_name)
        self.fields['compile_name'].textChanged.connect(suggest_icon)
        suggest_name()
        update_icon_preview()
        self.field(form, 'compile_output', '输出 A7Look（同时生成同名 DCP）', kind='save', filter='A7Look (*.a7look)')
        self.field(form, 'compile_hybrid_response', 'C2 Hybrid 响应文件', kind='file', filter='Response (*.json)',
                   value=str(ROOT / 'src/looks/looktool/r5fit/data/response.json'))
        run = W.QPushButton('开始生成')
        run.clicked.connect(lambda: (dialog.accept(), self.launch('compile_look', {
            'source': self.text('compile_source'), 'name': self.text('compile_name'),
            'output': self.text('compile_output'), 'model': self.text('compile_hybrid_response'),
            'include_menu_icon':include_icon.isChecked(),'menu_icon_text':self.text('compile_icon'),
            'input_space': input_space.currentData(),'output_space':output_space.currentData(),
            'bridge':self.text('compile_input_bridge')if input_space.currentData()=='custom'else None, 'passes': 12})))
        layout.addWidget(run)
        dialog.exec()

    def plugin_dialog(self):
        self.launch('plugin_install', {})


    def launch(self, action, arguments):
        if self.process is not None:
            return
        if action in ('firmware_build','firmware_factory_build'):
            source=str(arguments.get('sony_firmware')or'').strip()
            if not source or not Path(source).is_file():
                W.QMessageBox.information(self,'请选择本地固件','请先选择电脑上的官方 A7C II 2.01 BODYDATA.DAT，再生成固件。')
                return False
            arguments=dict(arguments,sony_firmware=source)
        if action=='firmware_build' and not (hasattr(self,'install_guide')and self.install_guide.pending=='firmware_build'):
            W.QMessageBox.information(self,'卡刷前先写入配置',
                '生成只处理电脑文件。'+reloadguide.PREFLASH_SETTINGS+
                '已授信的机身不必重新安装公钥；更新末尾不再运行额外配置脚本。')
        if action=='firmware_trust_prepare':
            from .firmwaretrust import validate
            try:validate(arguments)
            except (ValueError,OSError) as exc:
                W.QMessageBox.information(self,'请检查离线准备来源',str(exc));return
        if action in ('firmware_trust_install','firmware_trust_verify','firmware_trust_restore'):
            from .trustinstall import validate_request
            try:validate_request(action,arguments)
            except (ValueError,OSError,KeyError) as exc:
                W.QMessageBox.information(self,'请检查安装记录',str(exc));return
        if action=='ssh_verify_update' and not any(Path(arguments.get('workspace',''),n).is_file()for n in ('update.private.json','command.private.json')):
            W.QMessageBox.information(self,'尚无待核对的更新','请先完成本次 SSH 更新，再断电重开并核对。');return
        if action=='ssh_sound_custom':
            try:
                from .actions.sound import converted_file
                converted_file(arguments['sound_workspace'])
            except (ValueError,OSError,KeyError) as exc:
                W.QMessageBox.information(self,'请先准备声音',str(exc));return
        if action == 'sound_audition':
            from .actions.sound import has_conversion
            try:
                ready = has_conversion(arguments['workspace'])
            except (ValueError, OSError, KeyError) as exc:
                W.QMessageBox.warning(self, '声音工作区需要核对', str(exc));return
            if not ready:
                W.QMessageBox.information(self, '请先转换片段', '还没有转换好的声音。请先选择声音文件、设置起点和长度，点「转换所选片段」，成功后再试听。');return
        if action == 'driver_uninstall':
            answer = W.QMessageBox.question(self, '卸载相机驱动',
                '将备份并卸载 Sony 054C:0E8A／0336 的第三方驱动，让 Windows 重新识别相机。\n'
                '完成后可能需要拔插 USB，重新选择海量存储模式。此操作不修改相机固件。\n现在卸载？',
                W.QMessageBox.Yes | W.QMessageBox.Cancel, W.QMessageBox.Cancel)
            if answer != W.QMessageBox.Yes:
                return
        writing = action in jobs.POWER_ACTIONS
        if writing:
            target=arguments.get('look')or arguments.get('workspace')or''
            if action=='direct_looks_import':
                target='；'.join('自订 %s → %s'%(r['slot'],'恢复 ST 默认'if r['action']=='restore'else'写入 '+r['name'])for r in arguments.get('operations',[]))
            scope=('仅写入并保存所选刷前配置；之后保持开机，直接手动卡刷。\n'if action=='firmware_settings_install'else
                   '保存机身原始备份并安装公钥。\n'if action=='firmware_trust_install'else
                   '从本机首次授信备份恢复原厂公钥，撤销本工具授信。\n'if action=='firmware_trust_restore'else
                   '仅将更新器版本设为 2.00，随后手动卡刷恢复包。\n'if action in ('usb_restore_version','ssh_restore_version')else
                   '只修改版本资料。\n'if action=='usb_set_version'else
                   '按所选范围保存外观或快门声音，完成后按提示重开。\n')
            ssh_write=action in ('ssh_save_looks','ssh_sound_custom','ssh_sound_switch','ssh_apply_update','ssh_restore_version')
            connection='Wi-Fi / SSH' if ssh_write else 'USB'
            if ssh_write:
                target=('所选 %d 个滤镜槽位'%len(arguments['operations']) if action=='ssh_save_looks' else
                    '版本号 '+arguments['source_version']+' → 2.00（仅修改版本资料）' if action=='ssh_restore_version' else
                    {'electronic':'电子快门音效','mechanical':'机械快门音效','both':'电子与机械快门音效'}.get(arguments.get('selection'),'本次更新'))
            if action=='usb_restore_version':target='更新器版本资料 → 2.00；之后手动卡刷'
            if action=='usb_set_version':target='更新器版本资料 → '+arguments['target_version']
            firmware_label=(f'官方 2.01 或现有 3.10／{VERSION} 固件' if action=='firmware_settings_install' else
                '基于官方 2.01 的研究固件' if action in ('usb_restore_version','ssh_restore_version') else '固件 2.01')
            answer = W.QMessageBox.question(self, '开始相机写入',
                scope + '目标：' + str(target) + '\n请确认机身为 ILCE-7CM2、'+firmware_label+'，电量充足（建议至少 50%）。\n'
                '操作和读回期间保持供电、'+connection+' 连接，不要关机或断开连接。\n确认供电充足并开始？',
                W.QMessageBox.Yes | W.QMessageBox.Cancel, W.QMessageBox.Cancel)
            if answer != W.QMessageBox.Yes:
                return
            arguments = dict(arguments, power_confirmed=True)
            arguments.pop('battery', None)
        if action=='ssh_save_looks':self.settings['look_ssh_work']=arguments['workspace']
        if action=='ssh_restore_version':self.settings['factory_version_work']=arguments['workspace']
        if action=='usb_restore_version':self.settings['factory_usb_version_work']=arguments['workspace']
        if action=='firmware_trust_install':
            if not self.settings.get('trust_install_work'):self.settings['trust_install_work']=arguments['workspace']
        if action in ('firmware_trust_install','firmware_trust_restore'):
            self.settings['trust_latest_work']=arguments['workspace']
        if action in ('sound_import','sound_generate','sound_volume'):self.stop_sound_preview()
        if action=='direct_looks_import':self.settings['look_direct_work']=arguments['workspace']
        for key, field in self.fields.items():
            self.settings[key] = field.text()
        write_json(data_root() / 'desktop.json', self.settings)
        self.current_job = jobs.new_job(action, arguments)
        if action=='direct_looks_import' or (action=='direct_verify' and arguments.get('workspace')==self.settings.get('look_direct_work')):
            self.settings['look_job_dir']=str(self.current_job)
            write_json(data_root()/'desktop.json',self.settings)
        self.log_offset = 0
        self.log.clear()
        self.log_toggle.setChecked(True)
        self.camera_operation = action in jobs.CAMERA_ACTIONS or action == 'driver_install'
        for button in self.buttons:
            button.setEnabled(False)
        self.look_editor.setEnabled(False)
        self.stop.setEnabled(not self.camera_operation)
        self.progress.setRange(0, 0)
        self.status.setText('正在执行：' + action + '。详细日志持续保存。')
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
        if hasattr(self,'install_guide'):self.install_guide.refresh()
        return True

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
        self.refresh_status_dot()
        if self.process is None and (self._look_displayed_pending is not None or self.look_pending_state()):self.refresh_look_controls()
        # The status file also recovers completion if Qt missed its signal.
        if self.process is not None and self.process.state() == QtCore.QProcess.NotRunning:
            self.finished(self.process.exitCode(), self.process.exitStatus())

    def refresh_status_dot(self):
        state=('running' if self.process is not None else 'error' if self.status.text().startswith('操作停止') else
               'success' if self.progress.value()==100 else 'idle')
        if self.status_dot.property('state')!=state:
            self.status_dot.setProperty('state',state)
            self.status_dot.style().unpolish(self.status_dot);self.status_dot.style().polish(self.status_dot)

    def finished(self,code,exit_status):
        if self.process is None:return
        self.tail_log();path=self.current_job/'status.private.json'
        status=json.loads(path.read_text(encoding='utf-8'))if path.exists()else{}
        success=code==0 and status.get('phase')=='SUCCEEDED'
        action=status.get('action');result=status.get('result',{})
        if success and action in ('usb_prepare','connect'):self.settings['connection_verified']=True
        if success and action=='firmware_trust_verify':self.settings['trust_latest_work']=result['workspace']
        if success and action=='firmware_trust_install':self.remember_trust_install(result)
        if success and action in ('direct_looks_import','direct_verify')and result.get('mode')in ('install_all','look_import','slot_default'):
            self.settings['look_direct_work']=result['workspace'];self.settings.pop('look_resume_source',None)
        if success and result.get('next_baseline'):
            self.settings['ssh_update_baseline']=result['next_baseline']
        if success and action in ('firmware_build','firmware_factory_build')and result.get('baseline'):
            self.settings['ssh_update_baseline']=result['baseline']
        for key,field in self.fields.items():self.settings[key]=field.text()
        write_json(data_root()/'desktop.json',self.settings)
        waiting=success and reloadguide.required(action,result)
        sound_notice=reloadguide.sound_notice(action,result)if success else None
        message=result.get('message')or('读写已结束，请按弹窗重开相机。'if waiting else'操作完成。')
        if not success:message='操作停止：'+status.get('error','进程异常退出，退出码 '+str(code))+'。请导出诊断包。'
        if not success and sys.platform=='win32'and self.driver_step_failed(action)and status.get('error_type')!='ServiceExitUnconfirmed':message+=DRIVER_HINT
        if sound_notice:message=sound_notice['status']
        if success and action in ('firmware_build','firmware_factory_build')and result.get('signed'):
            message='固件已生成：'+result['candidate']+'。SD 卡只需要这份 BODYDATA.DAT。'
        self.status.setText(message)
        if success and action in ('sound_import','sound_volume'):
            self.sound_preview_status.setText('电脑声音已准备好 · 音量调整 %+.0f dB · 可试听或保存'%result.get('volume_gain_db',0))
        self.progress.setRange(0,100);self.progress.setValue(100 if success else 0)
        for button in self.buttons:button.setEnabled(True)
        self.stop.setEnabled(False);self.process.deleteLater();self.process=None
        self.refresh_status_dot()
        if success and action in ('direct_looks_import','direct_verify')and result.get('mode')in ('install_all','look_import','slot_default')and result.get('phase')in ('COMPLETED','AWAITING_RELOAD','LOADED','COMPLETE'):
            self.look_editor.set_operations([])
        self.refresh_look_controls();self.refresh_factory_controls();self.refresh_trust_controls()
        self.install_guide.finished(status,success);self.install_guide.refresh()
        driver_notice=connectionguide.completion(action,result)if success else None
        if driver_notice:self.status.setText(driver_notice[0]);W.QMessageBox.information(self,*driver_notice)
        elif success and action=='firmware_settings_install':
            self.status.setText('刷前配置已保存；拔 USB 后保持开机，直接手动卡刷。')
            W.QMessageBox.information(self,'刷前配置已保存',reloadguide.PREFLASH_SETTINGS)
        elif not success and status.get('error_type')=='ServiceExitUnconfirmed':
            W.QMessageBox.warning(self,'驱动步骤停止：尚未确认退出服务模式',status.get('error','请保留日志。'))
        elif sound_notice:W.QMessageBox.information(self,sound_notice['title'],sound_notice['text'])
        elif action=='usb_stability':
            if success:W.QMessageBox.information(self,'USB 只读检测通过',result.get('note','只读传输检测完成，没有写入相机。'))
            else:W.QMessageBox.warning(self,'USB 连接检测未完成',status.get('error','请查看日志并换线后重测。'))
        elif waiting:self.show_reload_guide(mode=action if action and action.startswith('sound_')else result.get('mode'))


    def process_error(self, error):
        if self.process and error == QtCore.QProcess.FailedToStart:
            self.log.appendPlainText(self.process.errorString())
            self.finished(-1, None)

    def open_job(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self.current_job or data_root())))

    def export_logs(self):
        job=self.current_job
        if not job:
            request=W.QFileDialog.getOpenFileName(self,'选择已有任务记录',
                str(data_root()/'runs'),'任务记录 (request.private.json)')[0]
            if not request:return
            job=Path(request).parent
        path = W.QFileDialog.getSaveFileName(self, '导出诊断包', 'a7c2-diagnostics.zip', 'ZIP (*.zip)')[0]
        if path:
            try:
                jobs.export_support(job, path)
            except Exception as exc:
                W.QMessageBox.warning(self, '导出失败', str(exc))

    def cancel_offline(self):
        if self.process and not self.camera_operation:
            self.process.terminate()

    def closeEvent(self, event):
        if self.process:
            W.QMessageBox.information(self, '任务仍在运行', '请等待当前任务结束后关闭。相机写入期间不要结束程序或拔线。')
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
    app.setWindowIcon(QtGui.QIcon(asset('mark.png')))
    app.setApplicationName('A7C2Tools')
    app.setOrganizationName('QAQLeonard')
    if '--smoke-test' not in sys.argv and not require_consent():
        return 0
    window = Window()
    window.show()
    if '--smoke-test'in sys.argv:
        for key in window.page_widgets:
            window.select_page(key);app.processEvents()
        window.select_page('install');QtCore.QTimer.singleShot(800,app.quit)
    return app.exec()
