"""Fixed migration removes temporary-curve hooks before retiring their code."""
import struct
import pytest
from looktool import fixedbankcode,photobuild,photofull,photoio


def predecessor(legacy):
    template=photoio.template()if legacy else photofull.template()
    cp=bytearray(0x1140b80)
    code=bytes.fromhex(template['code'])
    at=photobuild.CODE_VA-fixedbankcode.BASE
    cp[at:at+len(code)]=code
    for hook in template['hooks']:
        at=hook['offset'];raw=bytes.fromhex(hook['after'])
        cp[at:at+len(raw)]=raw
    if not legacy:
        for at,raw in fixedbankcode.NATIVE_GAMMA_HOOKS.items():cp[at:at+len(raw)]=raw
    else:
        struct.pack_into('<4I',cp,photobuild.DATA_FILE,photobuild.MAGIC,1,63,108)
    at=fixedbankcode.PROFILE_CHANGE_HOOK-fixedbankcode.BASE
    cp[at:at+6]=fixedbankcode.PROFILE_CHANGE_ORIGINAL
    return bytes(cp)


@pytest.mark.parametrize('legacy',[True,False])
def test_migration_removes_retired_gamma_calls_and_preserves_exact_inverse(legacy):
    source=predecessor(legacy)
    target,_,info=fixedbankcode.prepare(source)
    for at,raw in fixedbankcode.NATIVE_GAMMA_HOOKS.items():assert target[at:at+len(raw)]==raw
    restored=bytearray(target)
    for window in reversed(info['windows']):
        at=window['offset'];raw=bytes.fromhex(window['before_hex'])
        restored[at:at+len(raw)]=raw
    assert bytes(restored)==source


@pytest.mark.parametrize('legacy',[True,False])
@pytest.mark.parametrize('site',fixedbankcode.NATIVE_GAMMA_HOOKS)
def test_migration_does_not_overwrite_an_unrelated_gamma_hook(legacy,site):
    cp=bytearray(predecessor(legacy));cp[site]^=1
    with pytest.raises(ValueError,match='hook differs'):
        fixedbankcode.prepare(bytes(cp))


@pytest.mark.parametrize('site',fixedbankcode.NATIVE_GAMMA_HOOKS)
def test_fixed_inspection_rejects_surviving_retired_gamma_calls(site):
    _,patches,_=fixedbankcode.generate()
    cp=bytearray(0x1140b80)
    for at,raw in patches.items():cp[at:at+len(raw)]=raw
    old=next(h for h in photoio.template()['hooks']if h['offset']==site)
    cp[site:site+4]=bytes.fromhex(old['after'])
    with pytest.raises(ValueError,match='Fixed look consumer differs at '+hex(site)):
        fixedbankcode.inspect(bytes(cp))
