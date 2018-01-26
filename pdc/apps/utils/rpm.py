#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import re

_RE_PATTERNS = {
    'name': r'(?P<name>[^:]+)',
    'version': r'(?P<version>[^:]+)',
    'release': r'(?P<release>[^:]+)',
    'epoch': r'(?P<epoch>[0-9]+)',
    'arch': r'(?P<arch>[^:.-]+)',
}


def _compile_re(nvr_format):
    pattern = nvr_format.replace('.', '\\.')
    return re.compile((r'^(?:.*/)?' + pattern + r'$').format(**_RE_PATTERNS))


_RE_NVRE = _compile_re('{name}-{version}-{release}:{epoch}')
_RE_ENVR = _compile_re('{epoch}:{name}-{version}-{release}')
_RE_NEVR = _compile_re('{name}-{epoch}:{version}-{release}')
_RE_NVR = _compile_re('{name}-{version}-{release}')

_RE_NVREA = _compile_re('{name}-{version}-{release}:{epoch}.{arch}')
_RE_ENVRA = _compile_re('{epoch}:{name}-{version}-{release}.{arch}')
_RE_NEVRA = _compile_re('{name}-{epoch}:{version}-{release}.{arch}')
_RE_NVRAE = _compile_re('{name}-{version}-{release}.{arch}:{epoch}')
_RE_NVRA = _compile_re('{name}-{version}-{release}.{arch}')

_RE_NVREA_RPM = _compile_re('{name}-{version}-{release}:{epoch}.{arch}.rpm')
_RE_ENVRA_RPM = _compile_re('{epoch}:{name}-{version}-{release}.{arch}.rpm')
_RE_NEVRA_RPM = _compile_re('{name}-{epoch}:{version}-{release}.{arch}.rpm')
_RE_NVRAE_RPM = _compile_re('{name}-{version}-{release}.{arch}.rpm:{epoch}')
_RE_NVRAE_RPM2 = _compile_re('{name}-{version}-{release}.{arch}:{epoch}.rpm')
_RE_NVRA_RPM = _compile_re('{name}-{version}-{release}.{arch}.rpm')

_RE_LIST_NVRE = [_RE_NVRE, _RE_ENVR, _RE_NEVR]
_RE_LIST_NVR = [_RE_NVR]

_RE_LIST_NVRAE = [
    _RE_NVREA_RPM, _RE_ENVRA_RPM, _RE_NEVRA_RPM, _RE_NVRAE_RPM, _RE_NVRAE_RPM2,
    _RE_NVREA, _RE_ENVRA, _RE_NEVRA, _RE_NVRAE]

_RE_LIST_NVRA = [_RE_NVRA_RPM, _RE_NVRA]


def _match_first_or_none(what, regexes):
    for regex in regexes:
        result = regex.match(what)
        if result:
            return result.groupdict()

    return None


def _match_first(nvr_type, what, regexes_with_epoch, regexes_without_epoch):
    result = _match_first_or_none(what, regexes_with_epoch)
    if result:
        return result

    result = _match_first_or_none(what, regexes_without_epoch)
    if not result:
        raise ValueError("Invalid %s: %s" % (nvr_type, what))

    result['epoch'] = ''
    return result


def parse_nvr(nvre):
    """
    Split N-V-R into a dictionary.

    @param nvre: N-V-R[:E], E:N-V-R or N-E:V-R string
    @type nvre: str
    @return: {name, version, release, epoch}
    @rtype: dict
    """
    return _match_first('NVRE', nvre, _RE_LIST_NVRE, _RE_LIST_NVR)


def parse_nvra(nvra):
    """Split N-V-R.A[.rpm] into a dictionary.

    @param nvra: N-V-R[:E].A[.rpm], E:N-V-R.A[.rpm], N-V-R.A[.rpm]:E or N-E:V-R.A[.rpm] string
    @type nvra: str
    @return: {name, version, release, epoch, arch, src}
    @rtype: dict
    """
    result = _match_first('NVRA', nvra, _RE_LIST_NVRAE, _RE_LIST_NVRA)
    result['src'] = (result['arch'] == 'src')
    return result
