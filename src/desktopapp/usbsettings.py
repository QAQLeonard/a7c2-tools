"""Explicit pre-card-update settings preparation through the original USB API."""
from pathlib import Path
import struct
import sys

from .paths import ROOT, write_json
from .reloadguide import PREFLASH_SETTINGS


def targets(args):
    fields = {}
    if args.get('fl23'):
        fields.update({0x02cf1287: b'\x0a', 0x02cf1289: b'\x0b'})
    if args.get('vertical'):
        fields[0x02cf1906] = b'\0'
    if args.get('voice_cleanup'):
        fields.update({0x02cf0475: b'\1', 0x02cf13c5: b'\0'})
    if not fields:
        raise ValueError('请至少选择一项刷前配置')
    return fields


def plan(args, ap, ram, saved):
    from looktool import device_layout, devicesettings, voicelock, verticalpersist
    device_layout.structural_ap(ap)
    fields = targets(args)
    for key in fields:
        attr = 0x60 if key in (0x02cf1287, 0x02cf1289) else 0x40
        for records in (ram, saved):
            row = records[0].get(key)
            if row is None or row.attr != attr or len(row.data) != 1:
                raise ValueError('功能配置的原厂字段格式不符：' + hex(key))
    if args.get('vertical'):
        verticalpersist.field(ap, ram, True)
    if args.get('voice_cleanup'):
        voicelock.settings(ap, ram)
    devicesettings.require_save_preserves_unsaved(ram, saved, fields)
    return fields


class Owner:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=False)
        self.state = dict(schema='a7c2-usb-preflash-settings/1', phase='READING', journal=[],
            setting_writes=[], setting_save_attempted=False, program_writes=0,
            wbi_writes=0, reboot_performed=False, validation_hashes_added=False)
        self.save()

    def save(self, phase=None):
        if phase:
            self.state['phase'] = phase
        write_json(self.root/'settings-install.private.json', self.state)

    def record(self, event, **values):
        self.state['journal'].append(dict(event=event,
            **{key: value for key, value in values.items() if 'sha256' not in key}))
        self.save()

    def raw(self, name, data):
        (self.root/name).write_bytes(data)


def capture(camera, owner, label):
    records = []
    for name, memory in (('ram', True), ('saved', False)):
        raw = camera.snapshot(memory)
        owner.raw(label+'-'+name+'.bin', raw)
        records.append(camera.records(raw))
    return records


def apply(camera, owner, args, ap, before):
    from looktool import devicesettings
    fields = plan(args, ap, *before)
    owner.state['targets'] = {hex(key): value.hex() for key, value in fields.items()}
    owner.state['before'] = {name: {hex(key): rows[0][key].data.hex() for key in fields}
        for name, rows in zip(('ram', 'saved'), before)}
    owner.save('PREFLIGHT_COMPLETE')
    changed = [key for key, value in fields.items()
        if any(rows[0][key].data != value for rows in before)]
    owner.state['changed_keys'] = [hex(key) for key in changed]
    for key in changed:
        owner.record('setting_write_intent', key=hex(key), value_hex=fields[key].hex())
        camera.property_write(key, fields[key], set(fields))
        owner.state['setting_writes'].append(hex(key))
        owner.save()
        if camera.property_read(key) != fields[key]:
            raise ValueError('设置写入读回不符：' + hex(key))
    if changed:
        owner.state['setting_save_attempted'] = True
        owner.save('SAVING_SETTINGS')
        camera.save_settings()
        owner.record('setting_save_returned')
    after = capture(camera, owner, 'after-save')
    expected = {key: value.hex() for key, value in fields.items()}
    for old, rows in zip(before, after):
        devicesettings.compare(old, rows, expected, camera.core)
    owner.state['after'] = {name: {hex(key): rows[0][key].data.hex() for key in fields}
        for name, rows in zip(('ram', 'saved'), after)}
    owner.save('SETTINGS_SAVED')
    return fields


def run(args, job, *, factory=None):
    from .worker import setup_runtime
    setup_runtime()
    from looktool.devicesession import Camera, modules, invoke
    from looktool.power import require_power
    require_power(confirmed=args.get('power_confirmed', False))
    targets(args)
    owner = Owner(args['workspace'])
    write_json(Path(job)/'backend-workspace.private.json', dict(workspace=str(owner.root)))
    transport, _ = modules()
    transport.SERVICE_ATTEMPTS = 1
    try:
        with (factory or Camera)(args.get('expected_identity')) as camera:
            version = camera.read('/setting/updater/dat4')
            owner.state['version_hex'] = version.hex()
            owner.save()
            if version not in (b'\x01\x02', b'\x10\x03', b'\x11\x03'):
                raise ValueError('刷前配置仅支持官方 2.01 或现有 3.10／3.11；本次尚未写入设置')
            print('读取当前程序与设置，准备刷前配置…', flush=True)
            ap = camera.read('/usr/lib/appFw.so')
            cp = camera.read('/cp/cpapp-b.bin')
            owner.raw('appFw.so', ap)
            owner.raw('cpapp-b.bin', cp)
            camera.byte_checks = True
            owner.state['program_identity'] = camera.pin_programs(ap, cp)
            if camera.identity_pending:
                blob = (ROOT/'src/fl23/assets/runtime.so').read_bytes()
                def decode(raw):
                    parsed = camera.core.parse_native('runtime', raw)
                    parsed['model_index'] = struct.unpack_from('<I', raw, 48)[0]
                    return parsed
                proof = invoke(camera, blob, stage='lut-runtime-staged.so', request=None,
                    result='a7c2.runtime.result', contents=None, mode=0, decode=decode,
                    record=owner.record, save_raw=lambda raw: owner.raw('model-probe.bin', raw),
                    extras=('a7c2.probe.result',))
                camera.confirm_identity(proof)
            before = capture(camera, owner, 'before')
            print('通过原设置接口保存所选刷前配置…', flush=True)
            apply(camera, owner, args, ap, before)
        owner.state['normal_usb_returned'] = transport.wait_normal_return(15)
        if not owner.state['normal_usb_returned']:
            raise ValueError('配置已保存，普通 USB 返回尚未确认；请保留记录，不要重复写入')
        owner.save('SETTINGS_PREPARED_FOR_CARD')
        print(PREFLASH_SETTINGS,flush=True)
        return dict(workspace=str(owner.root), phase='SETTINGS_PREPARED_FOR_CARD',
            changed_keys=owner.state['changed_keys'], settings=owner.state['after'],
            normal_usb_returned=True, program_writes=0, wbi_writes=0,
            reboot_performed=False, card_update_required=True, post_restart_verified=False,
            message=PREFLASH_SETTINGS)
    except BaseException as error:
        owner.state.update(failed_during=owner.state['phase'],
            error_type=type(error).__name__, error=str(error))
        owner.save('NEEDS_REVIEW_NO_AUTOMATIC_REPLAY')
        raise
