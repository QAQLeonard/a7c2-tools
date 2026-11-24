def run(request_path):
    import json
    from pathlib import Path
    from desktopapp import VERSION,firmwarefactory
    request=json.loads(Path(request_path).read_text(encoding='utf-8'))
    report=firmwarefactory.build(request['arguments'],Path(request['job']))
    final=Path(report['candidate'])
    assert VERSION=='3.11' and final.name=='BODYDATA.DAT' and final.is_file()
    assert report['signed'] and report['original_body_byte_exact']
    assert report['update_header_version']=='2.01'
    assert report['signature_validation']['version']=='2.01'
    assert report['signature_validation']['plaintext_byte_readback']
    assert report['signature_validation']['rsa_signature_valid']
    assert [p.name for p in final.parent.iterdir()]==['BODYDATA.DAT']
    assert report['intermediate_files_removed']
    assert Path(report['build_record']).is_file()
    Path(request['report']).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return dict(version=VERSION,firmware_version='2.01',phase='FROZEN_FACTORY_DAT_BUILT',firmware=str(final),
        bytes=final.stat().st_size,original_body_byte_exact=True,signature_valid=True,
        final_plaintext_readback=True,camera_filename=True,output_only_BODYDATA=True,
        intermediate_files_removed=True,camera_io=False,physical_card_update_tested=False)
