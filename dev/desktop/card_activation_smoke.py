"""Guard removal of the rejected update-time hook and portrait menu edit."""
from pathlib import Path

def run():
    from desktopapp import VERSION,firmwarefeatures,firmwarelocal
    from desktopapp.paths import ROOT
    assert VERSION=='3.11'
    for name in ('src/desktopapp/cardsettings.py','src/desktopapp/native/card_settings.c',
                 'dev/firmware/build_card_body.py','src/looks/looktool/verticalmenu.py'):
        assert not(ROOT/name).exists()
    assert 'prepare_prefix'not in Path(firmwarelocal.__file__).read_text(encoding='utf-8')
    assert 'verticalmenu'not in Path(firmwarefeatures.__file__).read_text(encoding='utf-8')
    return dict(version=VERSION,card_activation_hook=False,native_portrait_menu=False,
        rejected_implementation_removed=True,camera_io=False,firmware_built=False,
        old_suites_repeated=False,validation_hashes_added=False)
