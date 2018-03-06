import os
import re
import collections
from glob import glob
from shutil import copyfile
from IPython.display import display, Markdown, HTML

from tf.fabric import Fabric

SOURCE = 'uruk'
VERSION = '1.0'
CORPUS = f'tf/{SOURCE}/{VERSION}'
SOURCE_DIR = 'sources/cdli'
IMAGE_DIR = f'{SOURCE_DIR}/images'
TEMP_DIR = '_temp'
REPORT_DIR = 'reports'

LIMIT = 20

PHOTO_TO = '{}/tablets/photos'
PHOTO_EXT = 'jpg'

TABLET_TO = '{}/tablets/lineart'
TABLET_EXT = 'pdf'

IDEO_TO = '{}/ideographs/lineart'
IDEO_EXT = 'jpg'

LOCAL_DIR = 'cdli-imagery'

PHOTO_URL = f'https://cdli.ucla.edu/dl/photo/{{}}_d.{PHOTO_EXT}'
# CDLI_URL = 'https://cdli.ucla.edu/search/archival_view.php?ObjectID='
CDLI_URL = (
    'https://cdli.ucla.edu/search/search_results.php?'
    'SearchMode=Text&ObjectID={}'
)

FLAGS = (
    ('damage', '#'),
    ('remarkable', '!'),
    ('written', ('!(', ')')),
    ('uncertain', '?'),
)

OUTER_QUAD_TYPES = {'sign', 'quad'}

CLUSTER_BEGIN = {'[': ']', '<': '>', '(': ')'}
CLUSTER_END = {y: x for (x, y) in CLUSTER_BEGIN.items()}
CLUSTER_KIND = {'[': 'uncertain', '(': 'properName', '<': 'supplied'}
CLUSTER_BRACKETS = dict((name, (bOpen, CLUSTER_BEGIN[bOpen]))
                        for (bOpen, name) in CLUSTER_KIND.items())

FLEX_STYLE = (
    'display: flex;'
    'flex-flow: row nowrap;'
    'justify-content: center;'
    'align-items: center;'
    'align-content: center;'
)

ITEM_STYLE = ('padding: 0.5rem;')


def dm(md):
    display(Markdown(md))


def _wrapCdli(piece, pNum):
    return (
        '<a title="to CDLI archival page" target="_blank"'
        f' href="{CDLI_URL.format(pNum)}">{piece}</a>'
    )


def _wrapPhoto(piece, pNum):
    return (
        '<a title="to higher resolution photo on CDLI" target="_blank"'
        f' href="{PHOTO_URL.format(pNum)}">{piece}</a>'
    )


class Cunei(object):
    def __init__(self, repoBase, repoRel, name):
        repoBase = os.path.expanduser(repoBase)
        repo = f'{repoBase}/{repoRel}'
        self.repo = repo
        self.version = VERSION
        self.sourceDir = f'{repo}/{SOURCE_DIR}'
        self.imageDir = f'{repo}/{IMAGE_DIR}'
        self.tempDir = f'{repo}/{TEMP_DIR}'
        self.reportDir = f'{repo}/{REPORT_DIR}'
        for cdir in (TEMP_DIR, REPORT_DIR):
            os.makedirs(cdir, exist_ok=True)
        corpus = f'{repo}/{CORPUS}'
        TF = Fabric(locations=[corpus], modules=[''], silent=True)
        api = TF.load('', silent=True)
        allFeatures = TF.explore(silent=True, show=True)
        loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
        TF.load(loadableFeatures, add=True, silent=True)
        self.api = api
        self._getTabletPhotos()
        self._getTabletImages()
        self._getIdeoImages()
        self.cwd = os.getcwd()
        cwdPat = re.compile(f'^.*/github/([^/]+)/([^/]+)((?:/.+)?)$', re.I)
        cwdRel = cwdPat.findall(self.cwd)
        if cwdRel:
            (thisOrg, thisRepo, thisPath) = cwdRel[0]
        else:
            cwdRel = None
        nbLink = (
            None if name is None or cwdRel is None else
            f'http://nbviewer.jupyter.org/github'
            f'/{thisOrg}/{thisRepo}/blob/master{thisPath}/{name}.ipynb'
        )
        transLink = (
            f'https://github.com/{repoRel}'
            '/blob/master/docs/transcription.md'
        )
        dm(
            f'''
**Documentation:**
[Feature docs]({transLink})
[Cunei API](https://github.com/{repoRel}/blob/master/docs/cunei.md)
[Text-Fabric API](https://github.com/Dans-labs/text-fabric)
'''
        )
        if nbLink:
            dm(
                f'''
Go to
[nbviewer]({nbLink})
to view this notebook with all its pdf images.
'''
            )

    def getSource(self, node, nodeType=None, lineNumbers=False):
        api = self.api
        F = api.F
        L = api.L
        sourceLines = []
        lineNumber = ''
        if lineNumbers:
            lineNumber = f'{F.srcLnNum.v(node):>5}: '
        sourceLines.append(f'{lineNumber}{F.srcLn.v(node)}')
        for child in L.d(node, nodeType):
            sourceLine = F.srcLn.v(child)
            lineNumber = ''
            if sourceLine:
                if lineNumbers:
                    lineNumber = f'{F.srcLnNum.v(child):>5}: '
                sourceLines.append(f'{lineNumber}{sourceLine}')
        return sourceLines

    def atfFromSign(self, n, flags=False):
        F = self.api.F
        Fs = self.api.Fs
        if F.otype.v(n) != 'sign':
            return '«no sign»'

        grapheme = F.grapheme.v(n)
        if grapheme == '…':
            grapheme = '...'
        primeN = F.prime.v(n)
        prime = ("'" * primeN) if primeN else ''

        variantValue = F.variant.v(n)
        variant = f'~{variantValue}' if variantValue else ''

        modifierValue = F.modifier.v(n)
        modifier = f'@{modifierValue}' if modifierValue else ''
        modifierInnerValue = F.modifierInner.v(n)
        modifierInner = f'@{modifierInnerValue}' if modifierInnerValue else ''

        modifierFirst = F.modifierFirst.v(n)

        repeat = F.repeat.v(n)
        if repeat is None:
            varmod = (
                f'{modifier}{variant}'
                if modifierFirst else f'{variant}{modifier}'
            )
            result = f'{grapheme}{prime}{varmod}'
        else:
            if repeat == -1:
                repeat = 'N'
            varmod = (
                f'{modifierInner}{variant}'
                if modifierFirst else f'{variant}{modifierInner}'
            )
            result = f'{repeat}({grapheme}{prime}{varmod}){modifier}'

        if flags:
            for (flag, char) in FLAGS:
                value = Fs(flag).v(n)
                if value:
                    if type(char) is tuple:
                        result += f'{char[0]}{value}{char[1]}'
                    else:
                        result += char

        return result

    def atfFromQuad(self, n, flags=False, outer=True):
        api = self.api
        E = api.E
        F = api.F
        Fs = api.Fs
        if F.otype.v(n) != 'quad':
            return '«no quad»'

        children = E.sub.f(n)
        if not children or len(children) < 2:
            return f'«quad with less than two sub-quads»'
        result = ''
        for child in children:
            nextChildren = E.op.f(child)
            if nextChildren:
                op = nextChildren[0][1]
            else:
                op = ''
            childType = F.otype.v(child)

            thisResult = (
                self.atfFromQuad(child, flags=flags, outer=False) if
                childType == 'quad' else self.atfFromSign(child, flags=flags)
            )
            result += f'{thisResult}{op}'

        variant = F.variantOuter.v(n)
        variantStr = f'~{variant}' if variant else ''

        flagStr = ''
        if flags:
            for (flag, char) in FLAGS:
                value = Fs(flag).v(n)
                if value:
                    if type(char) is tuple:
                        flagStr += f'{char[0]}{value}{char[1]}'
                    else:
                        flagStr += char

        if variant:
            if flagStr:
                if outer:
                    result = f'|({result}){variantStr}|{flagStr}'
                else:
                    result = f'(({result}){variantStr}){flagStr}'
            else:
                if outer:
                    result = f'|({result}){variantStr}|'
                else:
                    result = f'({result}){variantStr}'
        else:
            if flagStr:
                if outer:
                    result = f'|{result}|{flagStr}'
                else:
                    result = f'({result}){flagStr}'
            else:
                if outer:
                    result = f'|{result}|'
                else:
                    result = f'({result})'

        return result

    def atfFromOuterQuad(self, n, flags=False):
        api = self.api
        F = api.F
        nodeType = F.otype.v(n)
        if nodeType == 'sign':
            return self.atfFromSign(n, flags=flags)
        elif nodeType == 'quad':
            return self.atfFromQuad(n, flags=flags, outer=True)
        else:
            return '«no outer quad»'

    def atfFromCluster(self, n, seen=None):
        api = self.api
        F = api.F
        E = api.E
        if F.otype.v(n) != 'cluster':
            return '«no cluster»'

        typ = F.type.v(n)
        (bOpen, bClose) = CLUSTER_BRACKETS[typ]
        if bClose == ')':
            bClose = ')a'
        children = api.sortNodes(E.sub.f(n))

        if seen is None:
            seen = set()
        result = []
        for child in children:
            if child in seen:
                continue
            childType = F.otype.v(child)

            thisResult = (
                self.atfFromCluster(child, seen=seen) if childType == 'cluster'
                else self.atfFromQuad(child, flags=True) if childType == 'quad'
                else self.atfFromSign(child, flags=True)
                if childType == 'sign' else None
            )
            seen.add(child)
            if thisResult is None:
                dm(
                    f'TF: child of cluster has type {childType}:'
                    ' should not happen'
                )
            result.append(thisResult)
        return f'{bOpen}{" ".join(result)}{bClose}'

    def getOuterQuads(self, n):
        api = self.api
        F = api.F
        E = api.E
        L = api.L
        return [
            quad for quad in L.d(n)
            if (
                F.otype.v(quad) in OUTER_QUAD_TYPES and
                all(F.otype.v(parent) != 'quad' for parent in E.sub.t(quad))
            )
        ]

    def nodeFromCase(self, passage):
        api = self.api
        F = api.F
        L = api.L
        T = api.T
        section = passage[0:2]
        caseNum = passage[2].replace('.', '')
        column = T.nodeFromSection(section)
        if column is None:
            return None
        cases = [
            c for c in L.d(column, otype='case')
            if F.fullNumber.v(c) == caseNum
        ]
        if not cases:
            return None
        return cases[0]

    def caseFromNode(self, n):
        api = self.api
        F = api.F
        T = api.T
        section = T.sectionFromNode(n)
        if section is None:
            return None
        fullNumber = F.fullNumber.v(n)
        if fullNumber is None:
            return None
        return (section[0], section[1], fullNumber)

    def photo(self, ns, showLink=True, **options):
        api = self.api
        F = api.F
        if type(ns) is int:
            ns = [ns]
        result = []
        attStr = ' '.join(
            f'{key}="{value}"' for (key, value) in options.items()
        )
        for n in ns:
            nType = F.otype.v(n)
            if nType == 'tablet':
                pNum = F.catalogId.v(n)
                image = self.tabletPhotos.get(pNum, None)
                if image is None:
                    tabletStr = _wrapCdli('<code>{pNum}</code>', pNum)
                    thisResult = (
                        f'<span><b>no photo</b> for tablet {tabletStr}</span>'
                    )
                else:
                    theImage = self._useImage(image)
                    displayValue = 'block' if showLink else 'inline'
                    imageStr = (
                        f'<img src="{theImage}"'
                        f' style="display: {displayValue}; max-height: 200;" {attStr} />'
                    )
                    thisResult = _wrapPhoto(imageStr, pNum)
                if showLink:
                    thisResult = f'''
<div style="display: inline;">{thisResult} {self.cdli(n)}</div>
'''

                result.append(thisResult)
            else:
                result.append(
                    f'''
<span><b>no photos</b> for <code>{nType}</code>s</span>
'''
                )
        resultStr = f'</div>\n<div style="{ITEM_STYLE}">'.join(result)
        return HTML(
            f'''
        <div style="{FLEX_STYLE}">
            <div style="{ITEM_STYLE}">
                {resultStr}
            </div>
        </div>
'''
        )

    def lineart(self, ns, key=None, **options):
        api = self.api
        F = api.F
        if type(ns) is int:
            ns = [ns]
        result = []
        attStr = ' '.join(
            f'{key}="{value}"' for (key, value) in options.items()
        )
        for n in ns:
            nType = F.otype.v(n)
            if nType in OUTER_QUAD_TYPES:
                ideo = self.atfFromOuterQuad(n)
                image = self.ideo.get(ideo, None)
                if image is None:
                    result.append(
                        f'''
<span><b>no lineart</b> for ideograph <code>{ideo}</code></span>
'''
                    )
                else:
                    theImage = self._useImage(image)
                    result.append(
                        f'''
<img src="{theImage}" style="display: inline;" {attStr} />
'''
                    )
            elif nType == 'tablet':
                pNum = F.catalogId.v(n)
                images = self.tabletLineart.get(pNum, None)
                if images is None:
                    tabletStr = _wrapCdli('<code>{pNum}</code>', pNum)
                    thisResult = f' <b>no lineart</b> for tablet {tabletStr}'
                    result.append(thisResult)
                else:
                    image = images.get(key or '', None)
                    if image is None:
                        result.append(
                            f'''
<span><b>try</b>
<code>key='</code><i>k</i><code>'</code>
for <i>k</i> one of
<code>{'</code> <code>'.join(sorted(images.keys()))}</code>
</span>
'''
                        )
                    else:
                        theImage = self._useImage(image)
                        imageStr = (
                            f'<img src="{theImage}"'
                            f' style="display: inline;" {attStr} />'
                        )
                        thisResult = _wrapCdli(imageStr, pNum)
                        result.append(thisResult)
            else:
                result.append(
                    f'''
<span><b>no lineart</b> for <code>{nType}</code>s</span>
'''
                )
        resultStr = f'</div>\n<div style="{ITEM_STYLE}">'.join(result)
        return HTML(
            f'''
        <div style="{FLEX_STYLE}">
            <div style="{ITEM_STYLE}">
                {resultStr}
            </div>
        </div>
'''
        )

    def cdli(self, n):
        api = self.api
        F = api.F
        pNum = F.catalogId.v(n)
        return _wrapCdli('on CDLI', pNum)

    def _useImage(self, image):
        (imageDir, imageName) = os.path.split(image)
        localDir = f'{self.cwd}/{LOCAL_DIR}'
        if not os.path.exists(localDir):
            os.makedirs(localDir, exist_ok=True)
        localImage = f'{localDir}/{imageName}'
        if (
            not os.path.exists(localImage) or
            os.path.getmtime(image) > os.path.getmtime(localImage)
        ):
            copyfile(image, localImage)
        return f'{LOCAL_DIR}/{imageName}'

    def _getIdeoImages(self):
        ideoDir = IDEO_TO.format(self.imageDir)
        filePaths = glob(f'{ideoDir}/*.{IDEO_EXT}')
        ideo = {}
        for filePath in filePaths:
            (fileDir, fileName) = os.path.split(filePath)
            (base, ext) = os.path.splitext(fileName)
            ideo[base] = filePath
        self.ideo = ideo
        print(f'Found {len(ideo)} ideographs')

    def _getTabletImages(self):
        tabletDir = TABLET_TO.format(self.imageDir)
        filePaths = glob(f'{tabletDir}/*.{TABLET_EXT}')
        tabletLineart = {}
        pNumPat = re.compile('P[0-9]+')
        theKeys = collections.Counter()
        for filePath in filePaths:
            (fileDir, fileName) = os.path.split(filePath)
            (base, ext) = os.path.splitext(fileName)
            pNums = pNumPat.findall(base)
            if not pNums:
                print(f'skipped non-tablet "{fileName}"')
                continue
            pNum = pNums[0]
            key = base.replace('_l', '').replace(pNum, '')
            theKeys[key] += 1
            tabletLineart.setdefault(pNum, {})[key] = filePath
        self.tabletLineart = tabletLineart
        print(f'Found {len(tabletLineart)} tablet linearts')

    def _getTabletPhotos(self):
        photoDir = PHOTO_TO.format(self.imageDir)
        filePaths = glob(f'{photoDir}/*.{PHOTO_EXT}')
        tabletPhotos = {}
        for filePath in filePaths:
            (fileDir, fileName) = os.path.split(filePath)
            (pNum, ext) = os.path.splitext(fileName)
            tabletPhotos[pNum] = filePath
        self.tabletPhotos = tabletPhotos
        print(f'Found {len(tabletPhotos)} tablet photos')
