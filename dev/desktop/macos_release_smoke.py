"""Check the packaged Mac guide and native image tools without camera access."""
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch


def run():
    from desktopapp.worker import setup_runtime
    setup_runtime()
    import usb.core
    def no_device(*args,**kwargs):raise AssertionError('Offline check accessed physical USB')
    usb.core.find=no_device
    from PySide6 import QtWidgets as W
    from desktopapp import VERSION, imageedit, presets, window
    app=W.QApplication.instance() or W.QApplication([])
    with patch.object(window,'load_settings',return_value={}):view=window.Window(demo=True)
    try:
        view.timer.stop();guide=view.install_guide
        assert VERSION=='3.11'
        assert guide.steps.count()==3 and guide.driver_pane is None
        assert guide.driver_button is None and len(guide.panels)==1
        assert view.nav_items['drivers'].text()=='USB 连接'
        assert guide.steps.widget(0).isAncestorOf(view.fields['firmware_source'])
        assert not any('驱动' in label.text() for label in guide.findChildren(W.QLabel))
        assert not any(guide.isAncestorOf(button) for button in (
            view.page_widgets['drivers'].findChild(W.QPushButton,'action_usb_prepare'),))
        with patch.object(view,'launch',side_effect=AssertionError('Navigation accessed worker')):
            for expected in (1,2,0):
                guide.next.click();app.processEvents()
                assert guide.steps.currentIndex()==expected
            for key in ('drivers','firmware','advanced','install'):
                view.select_page(key);app.processEvents()
        assert guide.steps.widget(0).isAncestorOf(view.fields['firmware_source'])
        with patch.object(W.QMessageBox,'information') as popup:
            guide.build_button.click()
            assert popup.call_args.args[1]=='请选择本地固件'
        for action,button in (('firmware_trust_install',guide.trust_button),
                              ('firmware_settings_install',guide.config_button)):
            with patch.object(view,'launch',return_value=True) as launch:
                button.click();assert launch.call_args.args[0]==action
            guide.finished({'action':action},False)
        programs=imageedit.check_environment()
        import subprocess
        for program in programs.values():
            done=subprocess.run([str(program),'-V'],capture_output=True,text=True,timeout=15)
            assert done.returncode==0,(str(program),done.stderr)
            import struct
            data=program.read_bytes();at=32;minimum=None
            assert data[:4]==b'\xcf\xfa\xed\xfe'
            for _ in range(struct.unpack_from('<I',data,16)[0]):
                command,size=struct.unpack_from('<II',data,at)
                if command==0x32:minimum=struct.unpack_from('<I',data,at+12)[0]
                elif command==0x24:minimum=struct.unpack_from('<I',data,at+8)[0]
                at+=size
            assert minimum is not None and minimum<=0x000e0000,(str(program),minimum)
        fixture=os.environ.get('A7C2_MACOS_IMAGE_FIXTURE')
        assert fixture,'Synthetic filesystem fixture required'
        with tempfile.TemporaryDirectory(prefix='a7c2-mac-image-') as folder:
            folder=Path(folder);payload=folder/'sample data.txt';payload.write_bytes(b'Native Mac firmware image editor')
            imageedit.edit_images(fixture,{'usr':{'/sample.txt':dict(source=str(payload),mode=0o644)}},folder/'edited')
        assert len(presets.catalog())==6
        from looktool import lookfile
        for row in presets.catalog():
            document=lookfile.read(row['path'])
            assert document['name']==row['name'] and document.get('menu_icon')
            assert document.get('edit_native') and 'raw_profile' not in document
        root=Path(window.ROOT)
        assert not (root/'desktop-assets/profile-library-v1').exists()
        from desktopapp.actions.ssh import engine
        engine().executable(root/'desktop-assets/ssh/dropbear')
        assert (root/'desktop-assets/ssh/password.hash').is_file()
        assert (root/'desktop-assets/ssh/dropbear-LICENSE.txt').is_file()
        import runpy
        runpy.run_path(str(root/'dev/desktop/offline_smoke.py'))['check_firmware_packaging']()
        from desktopapp import trustworker
        with tempfile.TemporaryDirectory(prefix='a7c2-mac-compile-') as folder:
            built=trustworker.build(Path(folder)/'native',0,512,16384,b'',b'')
            assert built.is_file() and built.stat().st_size<=65536
        import torch
        assert torch.mm(torch.eye(2),torch.ones(2,1)).tolist()==[[1.0],[1.0]]
        from desktopapp.identity import signing_paths
        from Cryptodome.PublicKey import RSA
        private,public=signing_paths()
        assert RSA.import_key(private.read_bytes()).public_key().n==RSA.import_key(public.read_bytes()).n
        return dict(version=VERSION,steps=3,driver_step=False,default_looks=6,
                    native_image_tools=True,synthetic_image_edit=True,image_tool_minimum_macos='14.0',native_compile=True,numerical_library=True,
                    signing_identity=True,camera_ssh_assets=True,camera_io=False,screenshots=False)
    finally:
        view.process=None;view.close();view.deleteLater();app.processEvents()


if __name__=='__main__':
    if '--app' in sys.argv:
        import subprocess
        app=sys.argv[sys.argv.index('--app')+1]
        output=Path(sys.argv[sys.argv.index('--report')+1]).resolve()
        with tempfile.TemporaryDirectory(prefix='a7c2-mac-guide-') as folder:
            env=dict(os.environ,QT_QPA_PLATFORM='offscreen',A7C2_DESKTOP_DATA=folder,
                     A7C2_MACOS_RELEASE_SELFTEST=str(output))
            done=subprocess.run([app,'--color-self-test',str(output)],env=env,timeout=120)
            raise SystemExit(done.returncode)
    print(json.dumps(run(),ensure_ascii=False))
