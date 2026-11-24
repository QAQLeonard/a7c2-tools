"""Focused frozen numerical and color-resource check; no camera or UI access."""
from pathlib import Path
import sys

def run(resources_only=False):
    root=Path(__file__).resolve().parents[2]
    sys.path[:0]=[str(root/'src'),str(root/'src/looks')]
    import os
    if os.environ.get('A7C2_RELEASE_MATRIX'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/firmware_matrix.py'))['run'](
            os.environ['A7C2_RELEASE_MATRIX'])
    if os.environ.get('A7C2_MACOS_RELEASE_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/macos_release_smoke.py'))['run']()
    if os.environ.get('A7C2_FIRMWARE_OPTIONS_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/firmware_options_smoke.py'))['run'](
            os.environ['A7C2_FIRMWARE_OPTIONS_SELFTEST'])
    if os.environ.get('A7C2_CONNECTION_SETTINGS_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/connection_settings_smoke.py'))['run'](
            os.environ['A7C2_CONNECTION_SETTINGS_SELFTEST'])
    if os.environ.get('A7C2_MANUAL_FLOW_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/manual_flow_smoke.py'))['run'](
            os.environ['A7C2_MANUAL_FLOW_SELFTEST'])
    if os.environ.get('A7C2_SOUND_VOLUME_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/sound_volume_smoke.py'))['run'](
            os.environ['A7C2_SOUND_VOLUME_SELFTEST'])
    if os.environ.get('A7C2_FIRMWARE_SOUND_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/firmware_sound_smoke.py'))['run'](
            os.environ['A7C2_FIRMWARE_SOUND_SELFTEST'])
    if os.environ.get('A7C2_INSTALL_GUIDE_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/install_guide_smoke.py'))['run'](
            os.environ['A7C2_INSTALL_GUIDE_SELFTEST'])
    if os.environ.get('A7C2_RECOVERY_SOUND_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/recovery_sound_smoke.py'))['run'](
            os.environ['A7C2_RECOVERY_SOUND_SELFTEST'])
    if os.environ.get('A7C2_UNIFIED_API_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/unified_api_smoke.py'))['run'](
            os.environ['A7C2_UNIFIED_API_SELFTEST'])
    if os.environ.get('A7C2_TRUST_RESTORE_FAT_TIME_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/trust_restore_fat_time_smoke.py'))['run'](
            os.environ['A7C2_TRUST_RESTORE_FAT_TIME_SELFTEST'])
    if os.environ.get('A7C2_TRUST_RESTORE_DIAGNOSTICS_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/trust_restore_diagnostics_smoke.py'))['run'](
            os.environ['A7C2_TRUST_RESTORE_DIAGNOSTICS_SELFTEST'])
    if os.environ.get('A7C2_M4_ICON_API_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/m4_icon_api_smoke.py'))['run'](os.environ['A7C2_M4_ICON_API_SELFTEST'])
    if os.environ.get('A7C2_PREINSTALLED_SOUND_SELFTEST')=='1':
        import runpy
        return runpy.run_path(str(root/'dev/desktop/preinstalled_sound_smoke.py'))['run']()
    if os.environ.get('A7C2_FACTORY_FIRMWARE_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/factory_firmware_smoke.py'))['run'](os.environ['A7C2_FACTORY_FIRMWARE_SELFTEST'])
    if os.environ.get('A7C2_CARD_RECOVERY_SELFTEST')=='1':
        import runpy
        return runpy.run_path(str(root/'dev/desktop/card_recovery_smoke.py'))['run']()
    if os.environ.get('A7C2_NATIVE_FIRMWARE_SELFTEST'):
        import runpy
        return runpy.run_path(str(root/'dev/desktop/native_firmware_smoke.py'))['run'](os.environ['A7C2_NATIVE_FIRMWARE_SELFTEST'])
    if os.environ.get('A7C2_OUTPUT_DIRECTORY_SELFTEST')=='1':
        import runpy
        return runpy.run_path(str(root/'dev/desktop/output_directory_smoke.py'))['run']()
    if os.environ.get('A7C2_INSTALL_PACK_SELFTEST')=='1':
        import runpy
        return runpy.run_path(str(root/'dev/desktop/install_pack_smoke.py'))['run']()
    if os.environ.get('A7C2_M4_PORTRAIT_SELFTEST')=='1':
        import runpy
        return runpy.run_path(str(root/'dev/desktop/m4_portrait_smoke.py'))['run']()
    if os.environ.get('A7C2_SINGLE_USB_CARD_SELFTEST')=='1':
        import runpy
        return runpy.run_path(str(root/'dev/desktop/card_flow_smoke.py'))['run']()
    if os.environ.get('A7C2_CARD_ACTIVATION_SELFTEST')=='1':
        import runpy
        return runpy.run_path(str(root/'dev/desktop/card_activation_smoke.py'))['run']()
    if os.environ.get('A7C2_CARD_CONTRACT_SELFTEST')=='1':
        import runpy
        return runpy.run_path(str(root/'dev/desktop/card_smoke.py'))['run']()
    if os.environ.get('A7C2_LUT_SPACES_SELFTEST')=='1':
        from looktool import lutspaces,looklabels
        from desktopapp import VERSION
        import numpy as np
        opts=lutspaces.options()
        assert len(opts['inputs'])==37 and len(opts['outputs'])==9
        sample=np.array([[.1,.2,.3],[.8,.7,.6]])
        errors={}
        for key,_,_,_ in lutspaces.PROFILES:
            value=lutspaces.convert(sample,'srgb',key)
            errors[key]=float(abs(lutspaces.convert(value,key,'srgb')-sample).max())
            assert errors[key]<.0004
        assert looklabels.metadata('Custom unknown title')[1]['label']=='LUT'
        assert looklabels.metadata('Kodak UltraMax 400')[1]['label']=='K400'
        from looktool import dcpexport
        import tempfile
        folder=Path(tempfile.mkdtemp(prefix='lut-spaces-frozen-',dir=os.environ['TEMP']))
        source=folder/'identity.cube';source.write_text('LUT_3D_SIZE 2\n0 0 0\n1 0 0\n0 1 0\n1 1 0\n0 0 1\n1 0 1\n0 1 1\n1 1 1\n',encoding='utf-8')
        dcpexport.cube_profile(source,'Frozen Log DCP',folder/'look.dcp',input_space='slog3-sgamut3cine',output_space='rec709',dimensions=(12,16,16))
        assert (folder/'look.dcp').stat().st_size>1000
        return dict(version=VERSION,input_spaces=len(opts['inputs']),output_spaces=len(opts['outputs']),
            roundtrip=errors,default_icon='LUT',actual_Log_DCP_generated=True,camera_io=False,unmodified_legacy_checks_repeated=False)
    from desktopapp import VERSION,presets
    from looktool import r5fit,lookfile,editrecipe
    report=None;native_count=None;projection=None
    if not resources_only:
        report=r5fit.preflight()
        import numpy as np
        from edit_parameter_context import ParameterContext
        model=ParameterContext(r5fit.context())
        with np.load(r5fit.ROOT/'data/inputs.npz')as samples:native=model.base.color_only(samples['input'][:512])
        assert native.shape==(512,9,3)and np.isfinite(native).all();native_count=len(native)
        from concave_gamma import ConcaveGamma
        from gamma_global_correction import _c2_windows_global_quantizer
        shape=ConcaveGamma(model.axis,control_count=128,global_correction=True)
        _c2_windows_global_quantizer(shape)
        desired=shape.curve(shape.encode(model.gamma_y/16))*16
        desired[1:]+=np.sin(np.arange(1,128))*.75
        raw,projection=shape.quantize_global_raw(desired,return_audit=True)
        assert shape.audit_even(raw)['passed']
        model.build(matrix_payload=model.payload,cc1=model.cc1,gamma_y=raw)
    builtin=[];builtin_documents=[]
    for row in presets.catalog():
        doc=lookfile.read(row['path'])
        assert doc['name']==row['name']
        assert editrecipe.unpack(editrecipe.pack(doc['edit_native']))==doc['edit_native']
        builtin.append(doc['name'])
        builtin_documents.append(doc)
    from desktopapp.profilelibrary import location
    import json
    paired=location();paired_catalog=paired/'catalog.json'
    collection=json.loads(paired_catalog.read_text(encoding='utf-8'))if paired_catalog.is_file()else{}
    library=root/'desktop-assets/creative-look-library-v2'
    count=0;dcp_count=0
    if collection.get('schema')=='a7c2-install-looks/1':
        for row in collection['profiles']:
            doc=lookfile.read(paired/row['a7look'])
            assert doc['name']==row['name'] and doc.get('menu_icon') and 'raw_profile' not in doc
            lookfile.writer_document(doc);count+=1
        assert count==collection['count']==6
    elif collection.get('schema')=='a7c2-profile-library/2':
        from looktool import rawidentity,rawprofiles
        for row in collection['profiles']:
            doc=lookfile.read(paired/row['a7look']);other=lookfile.read(paired/row['menu_a7look'])
            assert {k:v for k,v in doc.items()if k!='menu_icon'}=={k:v for k,v in other.items()if k!='menu_icon'}
            assert doc['method']=='R5-C2-Hybrid-native12-grid5-stack3-20261110'
            assert rawidentity.source_bytes(doc['raw_profile'])==(paired/row['dcp']).read_bytes()
            assert rawprofiles.dcp_info(paired/row['dcp'])['profile']==doc['name']==row['name']
            count+=1;dcp_count+=1
        assert count==dcp_count==collection['count']
        if collection.get('distribution')=='windows-default-six':
            assert [r['name']for r in collection['profiles']]==builtin and count==6
    elif library.exists():
        plain=list((library/'Looks').rglob('*.a7look'));icons=list((library/'MenuIcons').rglob('*.a7look'))
        assert len(plain)==len(icons)==41
        for file in plain:
            doc=lookfile.read(file);other=lookfile.read(library/'MenuIcons'/file.relative_to(library/'Looks'))
            assert {k:v for k,v in doc.items()if k!='menu_icon'}=={k:v for k,v in other.items()if k!='menu_icon'}
            assert doc['method']=='R5-C2-Hybrid-native12-grid5-stack3-20261110'
            count+=1
    rebuilt=0
    if count and not resources_only:
        with np.load(r5fit.ROOT/'data/inputs.npz')as archive:input_rows=archive['input'][:64]
        for document in builtin_documents:
            assert document['method']=='R5-C2-Hybrid-native12-grid5-stack3-20261110'
            p=document['edit_native']['fitted']
            native=model.build(matrix_payload=bytes.fromhex(p['matrix_780f_hex']),cc1=np.asarray(p['cc1_direct_raw']),gamma_y=np.asarray(p['gamma_7806_y']))
            assert np.isfinite(native.color_only(input_rows)).all()
            rebuilt+=1
    dcp_export=None
    if dcp_count and not resources_only:
        import os,uuid
        from looktool import dcpexport,rawprofiles
        folder=Path(os.environ['TEMP'])/('a7c2-paired-frozen-'+uuid.uuid4().hex)
        folder.mkdir(parents=True)
        source=folder/'identity.cube'
        source.write_text('LUT_3D_SIZE 2\n0 0 0\n1 0 0\n0 1 0\n1 1 0\n0 0 1\n1 0 1\n0 1 1\n1 1 1\n',encoding='utf-8')
        output=folder/'Packaged DCP Probe.dcp'
        dcp_export=dcpexport.cube_profile(source,'Packaged DCP Probe',output,dimensions=(12,16,16))
        assert rawprofiles.dcp_info(output)['profile']=='Packaged DCP Probe'
        dcp_export['file']=str(output)
    return dict(version=VERSION,numerical=report,native_renderer_samples=native_count,global_gamma_projection=projection,
        resources_only=resources_only,builtins=builtin,builtin_native_rebuilt=rebuilt,updated_library_styles=count,
        paired_DCP_profiles=dcp_count,packaged_DCP_export=dcp_export,optimizer_full_budget_executed_here=False,camera_io=False)
