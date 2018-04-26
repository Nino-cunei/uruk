import sys
import os
import collections
import re
import operator
import pprint
from shutil import rmtree
from glob import glob
from functools import reduce
from tf.fabric import Fabric

# FLAGS

HELP = '''tfFromAtf.py version -FLAG

where FLAG is one of:

-p: parse only, no TF generation
-v: validate: parsing and TF generation and loading
    but the TF is put in a temp directory
-V: validate: parsing and TF generation but not loading
    but the TF is put in a temp directory
-x: suppress printing showcases for debug
-t: load and precompute TF (in production location)
-T: load and precompute TF (in temp location)
-h: print this help and quit
'''

doParse = True
doTf = True
doLoad = True
tfInTemp = False
debug = True

if len(sys.argv) <= 1:
    print(HELP)
    sys.exit()

VERSION = sys.argv[1]

FLAG = len(sys.argv) > 2 and sys.argv[2]
if FLAG:
    if FLAG == '-p':
        doTf = False
        doLoad = False
    elif FLAG == '-v':
        tfInTemp = True
    elif FLAG == '-V':
        tfInTemp = True
        doLoad = False
    elif FLAG == '-x':
        debug = False
    elif FLAG == '-t':
        doParse = False
        doTf = False
    elif FLAG == '-T':
        doParse = False
        doTf = False
        tfInTemp = True
    else:
        if FLAG != '-h':
            print(f'Unknown flag "{FLAG}"')
        print(HELP)
        sys.exit()

ORIGIN = 'cdli'
CORPUS = 'uruk'

REPO_DIR = os.path.expanduser(f'~/github/Nino-cunei/{CORPUS}')
SOURCE_DIR = f'{REPO_DIR}/sources/{ORIGIN}/transcriptions/{VERSION}'
META_DIR = f'{REPO_DIR}/sources/{ORIGIN}/meta/{VERSION}'
TEMP_DIR = f'{REPO_DIR}/_temp'
DEBUG_FILE = f'{TEMP_DIR}/cldi_uruk.txt'
REPORT_DIR = f'{REPO_DIR}/reports'
ERROR_FILE = f'{REPORT_DIR}/errors.tsv'
DIAG_FILE = f'{REPORT_DIR}/diagnostics.tsv'
TF_BASE = TEMP_DIR if tfInTemp else REPO_DIR
TF_DIR = f'{TF_BASE}/tf/{CORPUS}/{VERSION}'

if not os.path.exists(META_DIR):
    print(f'No directory {META_DIR}')
    print(f'Unknown version "{VERSION}"')
    sys.exit()

# -1 is unlimited

LIMIT = -1

SHOWCASES = set(
    '''
    P000025
    P000743
    P000736
    P000784
    P001687
    P002090
    P002113
    P002202
    P002771
    P002852
    P004639
    P004747
    P005112
    P006275
    P006284
    P006326
    P006427
    P006428
    P006437
    P250428
    P252175
    P252184
    P283915
    P325228
    P411604
    P411610
    P448701
    P448702
    P464118
    P464141
    P471695
    P499393
'''.strip().split()
)

BLACKLIST = set(
    '''
    P464118
    P471689
    P471682
    P471685
    P471683
    P471691
    P471694
    P471693
    P471688
    P471687
    P471692
    P471684
    P491489
    P471686
    P471690
    P431151
    P455567
    P456183
    P455718
    P455726
    P456095
    P456780
    P456795
    P456817
    P457754
    P457755
    P458281
    P458349
    P458394
    P458395
    P458434
    P458717
    P458792
    P458869
'''.strip().split()
)

commonMetaData = dict(
    dataset=CORPUS,
    version=VERSION,
    datasetName='Cuneiform tablets from the Uruk IV-III period',
    source='CLDI',
    sourceUrl='https://cdli.ucla.edu',
    encoders=(
        'CDLI (transcription),'
        'Cale Johnson (expertise)'
        'and Dirk Roorda (TF)'
    ),
    email1=(
        'https://www.universiteitleiden.nl'
        '/en/staffmembers/cale-johnson#tab-1'
    ),
    email2='dirk.roorda@dans.knaw.nl',
)
specificMetaData = dict(
    badNumbering=(
        'problematic line numbering:'
        ' 1=duplicate numbers; 2=wrong order'
    ),
    catalogId=(
        'identifier of tablet in catalog'
        ' (http://www.flutopedia.com/tablets.htm)'
    ),
    comments='links comment nodes to their targets',
    damage=(
        'indicates damage of signs or quads,'
        'corresponds to #-flag in transcription'
    ),
    excavation='excavation number of tablet',
    fragment='level between tablet and face',
    fullNumber=(
        'the combination of face type and column number on columns'
    ),
    grapheme='name of a grapheme (glyph)',
    identifier='additional information pertaining to the name of a face',
    modifier=(
        'indicates modifcation of a sign;'
        ' corresponds to sign@letter in transcription.'
        ' if the grapheme is a repeat, the modification'
        ' applies to the whole repeat.'
    ),
    modifierFirst=(
        'indicates the order between modifiers and variants'
        ' on the same object;'
        ' if 1, modifiers come before variants'
    ),
    modifierInner=(
        'indicates modifcation of a sign within a repeat'
        'corresponds to sign@letter in transcription'
    ),
    name='name of tablet',
    number='number of a column or line or case',
    op='operator connecting left to right operand in a quad',
    origNumber='contains the source value for number if it deviates',
    period='period that characterises the tablet corpus',
    prime='indicates the presence/multiplicity of a prime (single quote)',
    remarkable='corresponds to ! flag in transcription ',
    repeat=(
        'number indicating the number of repeats of a grapheme,'
        'especially in numerals; -1 comes from repeat N in transcription'
    ),
    srcLn='transcribed line',
    srcLnNum='line number in transcription file',
    sub=(
        'connects line or case with sub-cases,'
        ' quad with sub-quads;'
        ' clusters with sub-clusters'
    ),
    text='text of comment nodes',
    type=(
        'type of a face; type of a comment; type of a cluster;'
        'type of a sign'
    ),
    uncertain='corresponds to ?-flag in transcription',
    variant='allograph for a sign, corresponds to ~x in transcription',
    variantOuter='allograph for a quad, corresponds to ~x in transcription',
    written='corresponds to !(xxx) flag in transcription',
)
numFeatures = set(
    '''
    badNumbering
    damage
    prime
    remarkable
    repeat
    srcLnNum
    uncertain
'''.strip().split()
)

oText = {
    'levels': 'tablet,face,column,line,case,cluster,quad,comment,sign',
    'sectionFeatures': 'catalogId,fullNumber,number',
    'sectionTypes': 'tablet,column,line',
    'fmt:text-orig-full': '{grapheme}',
    'fmt:text-trans-plain': '{srcLn}\\n',
    'fmt:text-trans-full': '{srcLnNum}: {srcLn}\\n',
}

FACES = set(
    '''
    obverse
    reverse
    top
    bottom
    left
    seal
    surface
    edge
'''.strip().split()
)

COLUMN = set('''
    column
'''.strip().split())

COMMENTS = set('''
    #
    $
'''.strip().split())

LOWER = set('abcdefghijklmnopqrstuvwxyz')
UPPER = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

CLUSTER_BEGIN = {'[': ']', '<': '>', '(': ')'}
CLUSTER_END = {y: x for (x, y) in CLUSTER_BEGIN.items()}
CLUSTER_KIND = {'[': 'uncertain', '(': 'properName', '<': 'supplied'}

OPERATORS = set('''
    x
    %
    &
    .
    :
    +
'''.strip().split())

VARMOD = set('''
    ~
    @
'''.strip().split())

MODIFIERS = set(
    '''
    c
    f
    g
    s
    t
    n
    z
    k
    r
    h
    v
'''.strip().split()
)

HEAD_CHARS = set('''
    &
    @
    $
'''.strip().split())

TWEAK_HEADS = (
    ('@columm', '@column'),
    ('@column3', '@column 3'),
)

TWEAK_LINES01 = (('1.1(', '1. 1('), )
TWEAK_LINES02 = (((69856, '3.a'), '3.b'), )
TWEAK_LINES = ()

TWEAK_MATERIAL01 = (
    ('U2@~b', 'U2~b'),
    ('4"', "4'"),
    ('[,', ''),
    ('SA|L', 'SAL|'),
    ('~x(', '~v ('),
    ('~x', '~v'),
    (')|U', ') |U'),
    ('1N(02)', '1(N02)'),
    ('(1N', '1(N'),
    ('~A', '~a'),
    ('{', '('),
    ('}', ')'),
    (';', ','),
    ('sag-apin', 'sag-apin'),
    ('@inversum', '@v'),
    (('KI@', -1), 'KI#'),
)
TWEAK_MATERIAL02 = (('|)~a', '|)a'), )
TWEAK_MATERIAL = ()

linePat = re.compile("([0-9a-zA-Z.'-]+)\s*(.*)")
numPartsPat = re.compile('([0-9-]+|[a-zA-Z]+)')

stripCommas = re.compile('\s*,\s*')
repeatEscapePat = re.compile("([0-9N]+)\(([A-Za-z0-9@'~]+)\)")
repeatPat = re.compile('^«([^=]*)=([^»]*)»$')

writtenEscapePat = re.compile('!\(([^)]*)\)')
writtenRestorePat = re.compile('!◀([^▶]*)▶')

flagsPat = re.compile('^(.*)((?:!◀[^▶]*▶)|[!#?*])$')
modifierPat = re.compile('^(.*)@(.)$')
variantPat = re.compile('^(.*)~([a-wyz0-9]+)$')

operatorPat = re.compile(f'[{"".join(OPERATORS)}]')

pp = pprint.PrettyPrinter(indent=2, width=100, compact=False)

for cdir in (SOURCE_DIR, TEMP_DIR, REPORT_DIR, TF_DIR):
    os.makedirs(cdir, exist_ok=True)


def readMeta():
    excavationByTablet = {}
    excavationByNumber = collections.defaultdict(list)
    excPat = 'Exc'
    excavPat = 'Excavation no.:'
    excavStr = None
    transStr = 'Transliteration:'
    transStrE = 'Primary publication:'
    files = glob(f'{META_DIR}/*.txt')
    for f in files:
        (dirF, fileF) = os.path.split(f)
        (period, ext) = os.path.splitext(fileF)
        transFile = f'{SOURCE_DIR}/{fileF}'
        transSkip = True
        with open(f) as fh:
            with open(transFile, 'w') as wh:
                for (ln, line) in enumerate(fh):
                    line = line.rstrip('\n')
                    if line.startswith(transStrE):
                        transSkip = True
                    if not transSkip:
                        wh.write(f'{line}\n')
                    if line.strip() == '':
                        excavStr = None
                        if not transSkip:
                            wh.write('\n' * 2)
                        transSkip = True
                    elif line.startswith(transStr):
                        transSkip = False
                    elif line.startswith(excPat):
                        if not line.startswith(excavPat):
                            print(f'WARNING: {period}:{ln} SKIP "{line}"')
                            continue
                        excavStr = line.rsplit(':', maxsplit=1)[1].strip()
                    elif line[0] == '&':
                        comps = line[1:].split('=', 1)
                        tablet = comps[0].strip()
                        good = True
                        if excavStr is None:
                            print(
                                f'WARNING: {period}:{ln}'
                                f' NO EXCAVATION for "{tablet}"'
                            )
                            good = False
                        if tablet in excavationByTablet:
                            print(
                                f'WARNING: {period}:{ln} DUPLICATE "{tablet}"'
                            )
                            good = False
                        if good:
                            if excavStr != '':
                                excavationByTablet[tablet] = excavStr
                                excavationByNumber[excavStr].append(tablet)
    fileName = 'excavationByTablet.tsv'
    filePath = f'{REPORT_DIR}/{fileName}'
    with open(filePath, 'w') as fh:
        fh.write('tablet\texcavationNumbers\n')
        for (tablet, excavs) in sorted(excavationByTablet.items()):
            fh.write(f'{tablet}\t{excavs}\n')
    fileName = 'excavationByNumber.tsv'
    filePath = f'{REPORT_DIR}/{fileName}'
    with open(filePath, 'w') as fh:
        fh.write('excavationNumbers\ttablets\n')
        for (excavs, tablets) in sorted(excavationByNumber.items()):
            fh.write(f'{excavs}\t{",".join(tablets)}\n')
    print(
        f'{len(excavationByTablet)} tablets have one of'
        f' {len(excavationByNumber)} excavation numbers'
    )
    return excavationByTablet


def readCorpora():
    files = glob(f'{SOURCE_DIR}/*.txt')
    tablets = set()
    for f in files:
        skipTablet = False
        curTablet = ''
        (dirF, fileF) = os.path.split(f)
        (period, ext) = os.path.splitext(fileF)
        with open(f) as fh:
            for (ln, line) in enumerate(fh):
                line = line.rstrip('\n')
                if len(line) and line[0] == '&':
                    comps = line[1:].split('=', 1)
                    curTablet = comps[0].strip()
                    if curTablet in tablets or curTablet in BLACKLIST:
                        skipTablet = True
                    else:
                        skipTablet = False
                    tablets.add(curTablet)
                yield (skipTablet, period, curTablet, ln + 1, line)


errors = []
diags = []


def error(msg, info, p):
    errors.append((msg, info, p))


def diag(msg, info, p):
    diags.append((msg, info, p))


def parseCorpora(excavations):
    tablets = []
    tabletIndex = {}
    curTablet = None
    curFace = None
    curFragment = None
    curColumn = None
    curNums = None
    curLine = None
    prevNum = None
    prevPeriod = None

    for p in readCorpora():
        (skip, period, tablet, ln, line) = p
        if period != prevPeriod:
            print(f'{period:<10} at tablet {len(tablets):>5}')
            curTablet = None
            curFace = None
            curColumn = None
            curNums = None
            curLine = None
            prevNum = None
        prevPeriod = period
        if len(line) == 0:
            continue
        fc = line[0]
        if len(line) == 1:
            if not skip:
                if fc != ' ':
                    error('line: single character', '', p)
            continue
        if fc in HEAD_CHARS:
            for (pat, rep) in TWEAK_HEADS:
                if line.startswith(pat):
                    diag('tweak', f'"{pat}" => "{rep}"', p)
                    line = line.replace(pat, rep)
        sc = line[1]
        if fc == '&':
            comps = line[1:].split('=', 1)
            if len(comps) == 1:
                error('tablet: malformed name', '', p)
                tNum = f'{period}.{ln}'
                tName = tNum
            else:
                tNum = comps[0].strip()
                tName = comps[1].strip()
            if tNum in tabletIndex:
                (prevPeriod, prevLn) = tabletIndex[tNum]
                diag(
                    'tablet: duplicate name => skipped',
                    f'first one is {prevPeriod}:{prevLn}', p
                )
            else:
                if len(tablets) == LIMIT:
                    break
                if skip:
                    continue
                curTablet = {
                    'catalogId': tNum,
                    'name': tName,
                    'faces': [],
                    'period': period,
                    'srcLn': line,
                    'srcLnNum': ln,
                }
                if tNum in excavations:
                    curTablet['excavation'] = excavations[tNum]
                curFragment = None
                curFace = None
                curColumn = None
                curNums = None
                curLine = None
                prevNum = None
                tabletIndex[tNum] = (period, ln)
                tablets.append(curTablet)
        elif fc == '@':
            if skip:
                continue
            kindStr = line[1:].strip()
            if kindStr == 'tablet':
                pass
            else:
                comps = kindStr.split(maxsplit=1)
                kind = comps[0]
                ident = comps[1] if len(comps) > 1 else None
                if kind in FACES:
                    if curTablet is None:
                        error('face: outside tablet', f'@{kindStr}', p)
                    else:
                        curFace = {
                            'type': kind,
                            'columns': [],
                            'srcLn': line,
                            'srcLnNum': ln,
                        }
                        if ident:
                            curFace['identifier'] = ident
                        if curFragment is not None:
                            curFace['fragment'] = curFragment
                        curTablet['faces'].append(curFace)
                        curColumn = None
                        curNums = None
                        curLine = None
                        prevNum = None
                elif kind == 'object':
                    if curTablet is None:
                        error('object: outside tablet', f'@{kindStr}', p)
                    elif curFace is not None:
                        error('object: within face', f'@{kindStr}', p)
                    else:
                        curTablet.setdefault('comments', []).append({
                            'srcLn': line,
                            'srcLnNum': ln,
                            'type': 'object',
                            'text': ident,
                        })
                elif kind == 'fragment':
                    if curTablet is None:
                        error('fragment: outside tablet', f'@{kindStr}', p)
                    else:
                        curFragment = ident
                else:
                    if kind in COLUMN:
                        colNum = '1' if ident is None else ident
                        prime = False
                        if "'" in colNum:
                            prime = True
                            colNum = colNum.replace("'", '')
                        if curFace is None:
                            diag(
                                'column: outside face => inserted "@noface"',
                                f'@{kindStr}',
                                p,
                            )
                            curFace = {
                                'type': 'noface',
                                'columns': [],
                                'srcLn': line,
                                'srcLnNum': ln,
                            }
                            curTablet['faces'].append(curFace)
                            curColumn = None
                            curNums = None
                            curLine = None
                            prevNum = None
                        curColumn = {
                            'number': colNum,
                            'fullNumber': f'{curFace["type"]}:{colNum}',
                            'lines': [],
                            'srcLn': line,
                            'srcLnNum': ln,
                        }
                        curNums = set()
                        curLine = None
                        prevNum = None
                        if prime:
                            curColumn['prime'] = 1
                        curFace['columns'].append(curColumn)
                    else:
                        error('@specifier: unknown', f'@{kindStr}', p)
        elif fc == '>' and sc == '>':
            if skip:
                continue
            if curLine is None:
                error('crossref: no line before', '', p)
            else:
                comps = line[2:].split(maxsplit=2)
                doc = comps[0].strip()
                docLine = None if len(comps) < 2 else comps[1].strip()
                docFlag = None if len(comps) < 3 else comps[2].strip()
                if (
                    ' ' in doc or
                    docLine and ' ' in docLine or
                    docFlag and ' ' in docFlag or
                    docFlag and docFlag != '?'
                ):
                    error('crossref: malformed', '', p)
                else:
                    docLine = '' if docLine is None else f'.{docLine}'
                    docFlag = '' if docFlag is None else f':{docFlag}'
                    crossref = f'{doc}{docLine}{docFlag}'
                    prevCrossref = curLine.get('crossref', None)
                    newCrossref = (
                        crossref if prevCrossref is None else
                        f'{prevCrossref}\n{crossref}'
                    )
                    curLine['crossref'] = newCrossref
        elif fc in COMMENTS:
            if skip:
                continue
            target = (
                curLine if curLine else curColumn if curColumn else curFace
                if curFace else curTablet
            )
            if target is None:
                error('comment: outside tablet', '', p)
            else:
                target.setdefault('comments', []).append({
                    'srcLn': line,
                    'srcLnNum': ln,
                    'type': 'ruling' if fc == '$' else 'meta',
                    'text': line[1:].strip()
                })
        else:
            if skip:
                continue
            for (pat, rep) in TWEAK_LINES:
                if type(pat) is tuple:
                    (lineNum, pat) = pat
                else:
                    lineNum = None
                if (
                    line.startswith(pat)
                    and
                    (lineNum is None or ln == lineNum)
                ):
                    lnRep = f' on line {lineNum}'
                    diag('tweak', f'"{pat}" {lnRep} => "{rep}"', p)
                    line = line.replace(pat, rep)
            if curColumn is None:
                # diag(
                #    'line: outside column => inserted "@column 0"',
                #    '',
                #    p,
                # )
                curColumn = {
                    'number': '0',
                    'fullNumber': f'{curFace["type"]}:0',
                    'lines': [],
                    'srcLn': line,
                    'srcLnNum': ln,
                }
                curFace['columns'].append(curColumn)
                curNums = set()
                curLine = None
                prevNum = None
            match = linePat.match(line)
            origNumber = None
            if match is None:
                diag('line: missing number', '', p)
                origNumber = ''
                lineNumber = incNum(prevNum)
                prevNum = lineNumber
                material = line
            else:
                lineNumber = match.group(1).replace('.', '')
                prevNum = lineNumber
                material = match.group(2).strip()
            prime = False
            if "'" in lineNumber:
                prime = True
            if lineNumber in curNums:
                error(
                    'line: duplicate number in column',
                    f'"{lineNumber}"',
                    p,
                )
            if fc in LOWER or fc in UPPER:
                diag(
                    'line: number starting with a letter', f'"{lineNumber}"', p
                )
            quads = parseLine(material, p)
            curLine = {
                'number': lineNumber,
                'material': quads,
                'srcLn': line,
                'srcLnNum': ln,
            }
            if origNumber is not None:
                curLine['origNumber'] = ''
            if prime:
                curLine['prime'] = 1
            curColumn['lines'].append(curLine)
    print(f'{"total":<10} at tablet {len(tablets):>5}')

    casify(tablets)

    printErrors(diags, diag=True)
    printErrors(errors)

    if debug:
        debugResults(tablets)
        print('Showcases written to file')
    return tablets


def repeatEscapeRepl(match):
    repeat = match.group(1)
    if repeat == 'N':
        repeat = -1
    return f'«{repeat}={match.group(2)}»'


def writtenEscapeRepl(match):
    return f'!◀{match.group(1)}▶'


def parseLine(material, p):
    # tweak
    for (pat, rep) in TWEAK_MATERIAL:
        if type(pat) is tuple:
            (pat, pos) = pat
            if pos == 0:
                condition = material.startswith(pat)
                mark = ' (at start)'
            elif pos == -1:
                condition = material.endswith(pat)
                mark = ' (at end)'
        else:
            pos = None
            condition = pat in material
            mark = ''

        if condition:
            diag('tweak', f'"{pat}"{mark} => "{rep}"', p)
            if pos is None:
                material = material.replace(pat, rep)
            elif pos == 0:
                material = material.replace(pat, rep, 1)
            else:
                material = material[0:-len(pat)] + rep
    # remove the commas and transform the numerals
    material = stripCommas.sub(' ', material)
    material = repeatEscapePat.sub(repeatEscapeRepl, material)
    material = writtenEscapePat.sub(writtenEscapeRepl, material)
    # translate ... to …
    material = material.replace('...', '…')
    outerQuads = material.split()
    startPoints = {}
    clusters = []
    outerQuadStructs = []
    for (q, outerQuad) in enumerate(outerQuads):
        stop = False
        rest = outerQuad

        while not stop:
            fq = rest[0]
            if fq not in CLUSTER_BEGIN:
                stop = True
            else:
                rest = rest[1:]
                startPoints[fq] = q
            if rest == '':
                stop = True

        stop = rest == ''
        while not stop:
            lq = rest[-1]
            if lq in CLUSTER_END:
                rest = rest[0:-1]
            elif rest.endswith(')a'):
                lq = rest[-2]
                rest = rest[0:-2]
            if not (lq in CLUSTER_END):
                stop = True
            else:
                lqo = CLUSTER_END[lq]
                cKind = CLUSTER_KIND[lqo]
                start = startPoints.get(lqo, None)
                if start is None:
                    error(
                        'cluster: missing open bracket',
                        f'{lq} misses {lqo}',
                        p,
                    )
                else:
                    clusters.append((cKind, start, q))
                    del startPoints[lqo]
            if rest == '':
                stop = True
        quadInfo = {}
        if rest.startswith('|'):
            (rest, quadInfo) = getPieceInfo(outerQuad, rest, p, outer=True)
        outerQuadStruct = parseOuterQuad(rest, p)
        if quadInfo:
            outerQuadStruct.setdefault('info', {}).update(quadInfo)
        outerQuadStructs.append(outerQuadStruct)
    if startPoints:
        error(
            'cluster: missing closing bracket(s)',
            f'{sorted(startPoints.items())}',
            p,
        )

    result = {'quads': outerQuadStructs}
    if clusters:
        result['clusters'] = clusters
    return result


def getPieceInfo(quad, piece, p, inRepeat=False, outer=None, empty_ok=False):
    base = piece
    pieceInfo = dict()

    if '?#' in base:
        diag('flags: unusual order "?#"', f'"{base}" in "{quad}"', p)

    stop = False
    while base != '' and not stop:
        # flags
        splits = flagsPat.findall(base)
        if splits:
            items = pieceInfo.setdefault('flags', {})
            (base, itemStr) = splits[0]
            msg = 'flag: repeated'
            if itemStr == '#':
                if 'damage' in items:
                    error(msg, f'# in "{quad}"', p)
                items['damage'] = 1
            elif itemStr == '?':
                if 'uncertain' in items:
                    error(msg, f'? in "{quad}"', p)
                items['uncertain'] = 1
            elif itemStr == '!':
                if 'remarkable' in items:
                    error(msg, f'! in "{quad}"', p)
                items['remarkable'] = 1
            elif itemStr.startswith('!'):
                if 'written' in items:
                    error(msg, f'"{itemStr}" in "{quad}"', p)
                items['written'] = itemStr[2:-1]
            continue

        # modifiers
        modName = 'modifiersInner' if inRepeat else 'modifiers'
        splits = modifierPat.findall(base)
        if splits:
            items = pieceInfo.setdefault(modName, set())
            (base, itemStr) = splits[0]
            if itemStr not in MODIFIERS:
                error('modifier: unknown', f'"{itemStr}" in "{quad}"', p)
            else:
                if itemStr in items:
                    error(f'modifier: repeated', f'"{itemStr}" in "{quad}"', p)
                items.add(itemStr)
            # if we have already seen variants, then this modifier
            # is inside the variant: we need to mark this
            if 'variants' in pieceInfo or 'variantsOuter' in pieceInfo:
                pieceInfo['modifierFirst'] = 1
            continue

        # variants
        varName = 'variantsOuter' if outer else 'variants'
        splits = variantPat.findall(base)
        if splits:
            items = pieceInfo.setdefault(varName, set())
            (base, itemStr) = splits[0]
            if itemStr in items:
                diag('variant: repeated', f'"~{itemStr}" in "{quad}"', p)
            items.add(itemStr)

            continue

        # primes
        primeFound = False
        while base != '' and base[-1] == "'":
            primeFound = True
            base = base[0:-1]
            if 'prime' in pieceInfo:
                pieceInfo['prime'] += 1
            else:
                pieceInfo['prime'] = 1
        if primeFound:
            continue

        stop = True

    if base == '':
        if not empty_ok:
            diag(f'grapheme: empty', f'"{piece}" in "{quad}"', p)
        if 'variants' in pieceInfo:
            if outer is None:
                pieceInfo['variantsOuter'] = pieceInfo['variants']
                del pieceInfo['variants']
    return (base, pieceInfo)


def parseOuterQuad(quad, p):
    base = quad
    if base != '':
        if operatorPat.search(base):
            if base[0] != '|' and base[-1] != '|':
                diag(
                    'quad: not surrounded by "|"s', f'"{base}" in "{quad}"', p
                )
            elif base[0] != '|':
                diag('quad: missing start "|"', f'"{base}" in "{quad}"', p)
            elif base[-1] != '|':
                diag('quad: missing end "|"', f'"{base}" in "{quad}"', p)
        else:
            if base[0] == '|' and base[-1] == '|':
                diag(
                    'quad: simple quad surrounded by "|"s',
                    f'"{base}" in "{quad}"', p
                )
            elif base[0] == '|':
                diag('quad: spurious start "|"', f'"{base}" in "{quad}"', p)
            elif base[-1] == '|':
                diag('quad: spurious end "|"', f'"{base}" in "{quad}"', p)
        base = base.strip('|')
        if len(base) == 0:
            error('quad: empty', '"|"', p)

    (result, restPos) = parseBrackets(base, 0, False, p)
    if restPos < len(base):
        pb = base[0:restPos]
        pa = base[restPos:]
        error('quad: trailing characters', f'"{pb}▲{pa}"', p)
    result = associateVariants(result)
    return transformQuad(result, p)


def associateVariants(quads):
    newQuads = []
    for quad in quads:
        if type(quad) is str:
            if quad[0] in VARMOD:
                prevNewQuad = newQuads[-1]
                newQuads[-1] = [prevNewQuad, quad]
            else:
                newQuads.append(quad)
        else:
            newQuads.append(associateVariants(quad))
    return newQuads


def parseTerminal(string):
    return [] if string == '' else [string]


def parseBrackets(string, fromPos, wantClose, p):
    result = []
    stop = False
    ls = len(string)
    while fromPos < ls and not stop:
        firstOpen = string.find('(', fromPos)
        firstClose = string.find(')', fromPos)
        if firstOpen == -1:
            firstOpen = ls
        if firstClose == -1:
            firstClose = ls
        firstBracket = min((firstOpen, firstClose))
        if firstBracket == ls:
            before = string[fromPos:]
            bracket = ''
        else:
            before = string[fromPos:firstBracket]
            bracket = string[firstBracket]
        result.extend(parseTerminal(before))
        if bracket == ')':
            if wantClose:
                stop = True
                wantClose = False
            else:
                pb = string[0:firstBracket]
                pB = string[firstBracket]
                pa = string[firstBracket + 1:]
                error('quad: extra ")"', f'"{pb}▶{pB}◀{pa}"', p)
            fromPos = firstBracket + 1
        elif bracket == '(':
            (subResult, fromPos) = parseBrackets(
                string,
                firstBracket + 1,
                True,
                p,
            )
            result.append(subResult)
        else:
            fromPos = ls
    if wantClose:
        msg = 'quad: missing ")"'
        if fromPos >= ls:
            error(msg, f'after "{string}▲"', p)
        elif string[fromPos] != ')':
            error(msg, f'in "{string[0:fromPos]}▲{string[fromPos:]}"')
        else:
            fromPos += 1
    return (result, fromPos)


def transformQuad(quads, p):
    dest = []
    lastOp = None
    for quad in quads:
        if type(quad) is str:
            ls = len(quad)
            signDatas = []
            k = 0
            signs = operatorPat.split(quad)
            if signs[0] == '':
                signs = signs[1:]
                operator = quad[k] if k < ls else ''
                k += 1
                dest[-1]['op'] = operator
            if signs[-1] == '':
                signs = signs[0:-1]
                lastOp = quad[-1]
            for (g, sign) in enumerate(signs):
                (base, info) = getPieceInfo(
                    quad,
                    sign,
                    p,
                    empty_ok=g == 0,
                    outer=None,
                )
                k += len(sign)
                operator = quad[k] if k < ls else ''
                k += 1
                rInfo = {}
                if g == 0 and base == '':
                    if info:
                        target = dest[-1]
                        # if 'quads' in target:
                        #    target = target['quads'][-1]
                        target.setdefault('info', {}).update(info)
                else:
                    parts = repeatPat.findall(base)
                    signData = {}
                    if parts:
                        (n, base) = parts[0]
                        signData['repeat'] = n
                        (base, rInfo) = getPieceInfo(
                            quad, base, p, inRepeat=True, outer=False
                        )
                    if '«' in base or '»' in base:
                        error(
                            'grapheme: repeat not recognized',
                            f' "{sign}" => "{base}"',
                            p,
                        )
                    signData['grapheme'] = base
                    signData['type'] = 'ideograph'
                    if len(base) >= 2:
                        if base[0] == 'N' and base[1].isdecimal():
                            signData['type'] = 'numeral'
                    elif base == '…':
                        signData['type'] = 'ellipsis'
                    elif base == 'X':
                        signData['type'] = 'unknown'
                    info.update(rInfo)
                    if info:
                        signData['info'] = info
                    if operator != '':
                        signData['op'] = operator
                    signDatas.append(signData)
            if lastOp:
                if len(signDatas) != 0:
                    signDatas[-1]['op'] = lastOp

            if len(signDatas):
                thisSignData = (
                    signDatas[0] if len(signDatas) == 1 and not lastOp else {
                        'quads': signDatas
                    }
                )
                dest.append(thisSignData)
        else:
            subQuad = transformQuad(quad, p)
            target = dest
            if len(target):
                lastDest = target[-1]
                if 'quads' in lastDest and 'op' in lastDest['quads'][-1]:
                    target = lastDest['quads']
            target.append(subQuad)
    result = (dest[0] if len(dest) == 1 else {'quads': dest})
    return result


def incNum(x):
    return str(int(x) + 1)


def casify(tablets):
    for tablet in tablets:
        curTablet = tablet
        tabletName = tablet.get('catalogId', '')
        for face in tablet.get('faces', []):
            for column in face.get('columns', []):
                lines = column.get('lines', None)
                if lines is not None:
                    (cases, badNumbering,
                     badNumbers) = putInCases(lines, curTablet)
                    if badNumbering:
                        column['badNumbering'] = badNumbering
                        srcLn = column['srcLnNum']
                        srcLine = column['srcLn']
                        period = curTablet.get('period', None)
                        info = (
                            'duplicates'
                            if badNumbering == 1 else 'wrong order'
                            if badNumbering == 2 else 'unspecified'
                        )
                        diag(
                            f'column: numbering: {info}', badNumbers,
                            (False, period, tabletName, srcLn, srcLine)
                        )
                    column['lines'] = cases


def numVal(n):
    if n.isdigit():
        return f'{int(n):0>7.1f}'
    comps = n.split('-', 1)
    if len(comps) == 2:
        (n1, n2) = comps
        if n1.isdigit() and n2.isdigit():
            return f'{(int(n1) + int(n2))/2:0>7.1f}'
        else:
            return n
    else:
        return n


def hKey(numParts):
    return tuple(numVal(n) for n in numParts)


def putInCases(lines, curTablet):
    cases = collections.OrderedDict()
    badNumbering = 0
    numbers = []
    badNumbers = None
    for line in lines:
        numParts = numPartsPat.findall(line['number'])
        if len(numParts):
            numbers.append(tuple(numParts))
        else:
            numbers.append(('', ))
        badNumbering = (
            1 if len(set(numbers)) != len(numbers) else 2
            if numbers != sorted(numbers, key=hKey) else 0
        )
        if badNumbering:
            badNumbers = ', '.join('.'.join(num) for num in numbers)
    if badNumbering:
        for (i, line) in enumerate(lines):
            cases[str(i + 1)] = line
    else:
        for line in lines:
            numParts = numPartsPat.findall(line['number'])
            if len(numParts):
                target = cases
                for (i, numPart) in enumerate(numParts[0:-1]):
                    reshapeTarget(target, curTablet)
                    target = target.setdefault(
                        ''.join(numParts[0:i+1]), collections.OrderedDict()
                    )
                lastPart = ''.join(numParts)
                reshapeTarget(target, curTablet)
                target[lastPart] = line
            else:
                cases[''] = line
    return (cases, badNumbering, badNumbers)


def reshapeTarget(target, curTablet):
    if 'material' in target:
        # this happens if you have a numbering like
        # 1  material 1
        # 1a material 1a
        # 1b material 1b
        srcLn = target['srcLnNum']
        srcLine = target['srcLn']
        period = curTablet.get('period', '')
        tabletName = curTablet.get('catalogId', '')
        diag(
            'case: has sub-cases AND material',
            '',
            (False, period, tabletName, srcLn, srcLine),
        )
        existing = {}
        existing.update(target)
        target.clear()
        target[''] = existing


def debugResults(tablets):
    with open(DEBUG_FILE, 'w') as fh:
        pq = pprint.PrettyPrinter(
            indent=2, width=100, compact=False, stream=fh
        )
        pq.pprint([
            tablet for tablet in tablets if tablet['catalogId'] in SHOWCASES
        ])


def printErrors(errors, diag=False):
    fileName = DIAG_FILE if diag else ERROR_FILE
    ErrorStr = 'Diagnostic' if diag else 'Error'
    errorStr = 'diagnostic' if diag else 'error'
    ErrorsStr = f'{ErrorStr}s'
    errorsStr = f'{errorStr}s'
    if not errors:
        print(f'OK, no {errorsStr}')
        if os.path.exists(fileName):
            os.remove(fileName)
    else:
        errorGroups = {}
        for (msg, info, p) in errors:
            errorGroups.setdefault(msg, []).append((p, info))
        print(f'{ErrorsStr}')
        fieldNames = '''
            skip
            period
            tablet
            ln
            line
            msg
            info
        '''.strip().split()
        nFields = len(fieldNames)
        fmt = ('{}\t' * (nFields - 1)) + '{}\n'
        total = 0
        with open(fileName, 'w') as fh:
            fh.write(fmt.format(*fieldNames))
            for (msg, data) in sorted(
                errorGroups.items(), key=lambda x: (len(x[1]), x[0])
            ):
                total += len(data)
                for (p, info) in data:
                    fh.write(fmt.format(*p, msg, info))
                print(f'\t{len(data):>4} x {msg}')
        print(f'{total} {errorsStr}')


def makeTf(tablets):
    cur = collections.Counter()
    curSlot = 0
    context = []
    nodeFeatures = collections.defaultdict(dict)
    edgeFeaturesV = collections.defaultdict(
        lambda: collections.defaultdict(dict)
    )
    edgeFeatures = collections.defaultdict(
        lambda: collections.defaultdict(set)
    )
    oSlots = collections.defaultdict(set)

    def doTablet(tablet):
        nodeType = 'tablet'
        cur[nodeType] += 1
        curNode = cur[nodeType]
        for ft in '''
            catalogId
            name
            period
            excavation
            srcLn
            srcLnNum
        '''.strip().split():
            if ft in tablet:
                nodeFeatures[ft][(nodeType, curNode)] = tablet[ft]
        context.append((nodeType, curNode))
        doComments(tablet, 'tablet')
        faces = tablet.get('faces', [])
        for face in faces:
            doFace(face)
        if not faces:
            doEmptySign()
        context.pop()

    def doFace(face):
        nodeType = 'face'
        cur[nodeType] += 1
        curNode = cur[nodeType]

        for ft in '''
            type
            identifier
            fragment
            srcLn
            srcLnNum
        '''.strip().split():
            if ft in face:
                nodeFeatures[ft][(nodeType, curNode)] = face[ft]

        context.append((nodeType, curNode))
        doComments(face, 'face')
        columns = face.get('columns', [])
        for column in columns:
            doColumn(column)
        if not columns:
            doEmptySign()
        context.pop()

    def doColumn(column):
        nodeType = 'column'
        cur[nodeType] += 1
        curNode = cur[nodeType]
        for ft in '''
            number
            prime
            fullNumber
            badNumbering
            srcLn
            srcLnNum
        '''.strip().split():
            if ft in column:
                nodeFeatures[ft][(nodeType, curNode)] = column[ft]
        context.append((nodeType, curNode))
        doComments(column, 'column')
        lines = column.get('lines', {})
        doLines(lines)
        if not lines:
            doEmptySign()
        context.pop()

    def doLines(lines):
        nodeType = 'line'
        for (lineNum, lineData) in lines.items():
            cur[nodeType] += 1
            curNode = cur[nodeType]
            nodeFeatures['number'][(nodeType, curNode)] = lineNum
            context.append((nodeType, curNode))
            if 'material' in lineData:
                doTerminalCase(lineData, 'line', curNode)
            else:
                doCases(lineData, 'line', curNode)
            context.pop()

    def doTerminalCase(caseData, nodeType, curNode):
        for ft in '''
            crossref
            origNumber
            prime
            srcLn
            srcLnNum
        '''.strip().split():
            if ft in caseData:
                nodeFeatures[ft][(nodeType, curNode)] = caseData[ft]
        nodeFeatures['terminal'][(nodeType, curNode)] = 1
        material = caseData.get('material', {})
        doComments(caseData, nodeType)
        hasQuads = doClusters(material)
        if not material or not hasQuads:
            doEmptySign()

    def doCases(cases, parentType, parentNode):
        nodeType = 'case'
        if 'material' in cases:
            doTerminalCase(cases, parentType, parentNode)
        else:
            for (caseNr, caseData) in cases.items():
                cur[nodeType] += 1
                curNode = cur[nodeType]
                nodeFeatures['number'][(nodeType, curNode)] = caseNr
                edgeFeatures['sub'][(parentType,
                                     parentNode)].add((nodeType, curNode))
                context.append((nodeType, curNode))
                doCases(caseData, nodeType, curNode)
                context.pop()

    def doComments(thing, thingType):
        nodeType = 'comment'
        for comment in thing.get('comments', []):
            cur[nodeType] += 1
            curNode = cur[nodeType]
            for ft in '''
                type
                text
                srcLn
                srcLnNum
            '''.strip().split():
                if ft in comment:
                    nodeFeatures[ft][(nodeType, curNode)] = comment[ft]
            edgeFeatures['comments'][(thingType,
                                      cur[thingType])].add((nodeType, curNode))
            context.append((nodeType, curNode))
            doEmptySign()
            context.pop()

    def doClusters(material):
        clusters = material.get('clusters', [])
        startClusters = collections.defaultdict(list)
        endClusters = collections.defaultdict(list)
        for (kind, fromQuad, toQuad) in sorted(
            clusters, key=lambda x: (x[1], -x[2], x[0])
        ):
            startClusters[fromQuad].append(kind)
            endClusters[toQuad + 1].append(kind)
        quads = material.get('quads', [])
        (prevQuad, prevType, prevNode) = (None, None, None)
        nodeType = 'cluster'
        for (q, quad) in enumerate(quads):
            if q in endClusters:
                for kind in endClusters[q]:
                    context.pop()
            if q in startClusters:
                for kind in startClusters[q]:
                    cur[nodeType] += 1
                    curNode = cur[nodeType]
                    nodeFeatures['type'][(nodeType, curNode)] = kind
                    for (cNodeType, cNode) in context:
                        if cNodeType == nodeType:
                            edgeFeatures['sub'][(nodeType, cNode)].add(
                                (nodeType, curNode)
                            )
                    context.append((nodeType, curNode))
            (prevType, prevNode) = doQuad(
                q,
                quad,
                prevQuad,
                prevType,
                prevNode,
                None,
                None,
            )
            for (cNodeType, cNode) in context:
                if cNodeType == nodeType:
                    edgeFeatures['sub'][(nodeType,
                                         cNode)].add((prevType, prevNode))
            prevQuad = quad
        q = len(quads)
        if q in endClusters:
            for kind in endClusters[q]:
                context.pop()
        return len(quads)

    def doQuad(q, quad, prevQuad, prevType, prevNode, parentType, parentNode):
        if 'grapheme' in quad:
            (nodeType, curNode) = doSign(quad)
        else:
            nodeType = 'quad'
            cur[nodeType] += 1
            curNode = cur[nodeType]
        if parentType is not None:
            edgeFeatures['sub'][(parentType,
                                 parentNode)].add((nodeType, curNode))
        if q > 0:
            op = prevQuad.get('op', None)
            if op is not None:
                edgeFeaturesV['op'][(prevType, prevNode)][(nodeType,
                                                           curNode)] = op
        if 'quads' in quad:
            context.append((nodeType, curNode))
            doInfo(quad, curNode, nodeType)
            (pQuad, pType, pNode) = (None, None, None)
            for (iq, iquad) in enumerate(quad['quads']):
                (pType, pNode) = doQuad(
                    iq, iquad, pQuad, pType, pNode, nodeType, curNode
                )
                pQuad = iquad
            context.pop()
        return (nodeType, curNode)

    def doSign(sign):
        nonlocal curSlot
        nodeType = 'sign'
        curSlot += 1
        for ft in '''
            grapheme
            type
            repeat
        '''.strip().split():
            if ft in sign:
                nodeFeatures[ft][(nodeType, curSlot)] = sign[ft]
        doInfo(sign, curSlot, nodeType)
        for (nt, curNode) in context:
            oSlots[(nt, curNode)].add(curSlot)
        return (nodeType, curSlot)

    def doEmptySign():
        doSign({'grapheme': '', 'type': 'empty'})

    def doInfo(data, node, nodeType):
        infoData = data.get('info', {})
        if 'prime' in infoData:
            nodeFeatures['prime'][(nodeType, node)] = infoData['prime']
        if 'variants' in infoData:
            nodeFeatures['variant'][(nodeType,
                                     node)] = ','.join(infoData['variants'])
        if 'variantsOuter' in infoData:
            nodeFeatures['variantOuter'][(nodeType, node)] = ','.join(
                infoData['variantsOuter']
            )
        if 'flags' in infoData:
            for (flag, value) in infoData['flags'].items():
                nodeFeatures[flag][(nodeType, node)] = value
        if 'modifiers' in infoData:
            nodeFeatures['modifier'][(nodeType,
                                      node)] = ','.join(infoData['modifiers'])
        if 'modifiersInner' in infoData:
            nodeFeatures['modifierInner'][(nodeType, node)] = ','.join(
                infoData['modifiersInner']
            )
        if 'modifierFirst' in infoData:
            nodeFeatures['modifierFirst'][(nodeType, node)] = 1

    print('Collecting nodes, edges and features')
    for (i, tablet) in enumerate(tablets):
        sys.stdout.write(f'\rtablet {i+1:>5}')
        doTablet(tablet)
    print('')
    if len(context):
        print('Context:', context)

    print(f'\n{curSlot:>7} x slot')
    for (nodeType, amount) in sorted(cur.items(), key=lambda x: (x[1], x[0])):
        print(f'{amount:>7} x {nodeType}')

    nValues = reduce(
        operator.add, (len(values) for values in nodeFeatures.values()), 0
    )
    print(f'{len(nodeFeatures)} node features with {nValues} values')
    print(f'{len(oSlots)} nodes linked to slots')

    print('Compiling TF data')
    print(f'Building warp feature otype')
    nodeOffset = {'sign': 0}
    oType = {}
    n = 1
    for k in range(n, curSlot + 1):
        oType[k] = 'sign'
    n = curSlot + 1
    for (nodeType, amount) in sorted(cur.items(), key=lambda x: (x[1], x[0])):
        nodeOffset[nodeType] = n - 1
        for k in range(n, n + amount):
            oType[k] = nodeType
        n = n + amount
    print(f'{len(oType)} nodes')

    print('Filling in the nodes and edges for features')
    newNodeFeatures = collections.defaultdict(dict)
    newEdgeFeatures = collections.defaultdict(
        lambda: collections.defaultdict(dict)
    )
    for (ft, featureData) in nodeFeatures.items():
        newFeatureData = {}
        for ((nodeType, node), value) in featureData.items():
            newFeatureData[nodeOffset[nodeType] + node] = value
        newNodeFeatures[ft] = newFeatureData
    for (ft, featureData) in edgeFeaturesV.items():
        newFeatureData = {}
        for ((nodeType, node), targets) in featureData.items():
            for ((targetType, targetNode), value) in targets.items():
                newFeatureData.setdefault(
                    nodeOffset[nodeType] + node, {}
                )[nodeOffset[targetType] + targetNode] = value
        newEdgeFeatures[ft] = newFeatureData
    for (ft, featureData) in edgeFeatures.items():
        newFeatureData = {}
        for ((nodeType, node), targets) in featureData.items():
            for (targetType, targetNode) in targets:
                newFeatureData.setdefault(
                    nodeOffset[nodeType] + node, set()
                ).add(nodeOffset[targetType] + targetNode)
        newEdgeFeatures[ft] = newFeatureData
    newOslots = {}
    for ((nodeType, node), slots) in oSlots.items():
        newOslots[nodeOffset[nodeType] + node] = slots

    nodeFeatures = newNodeFeatures
    nodeFeatures['otype'] = oType
    edgeFeatures = newEdgeFeatures
    edgeFeatures['oslots'] = newOslots

    print(f'Node features: {" ".join(nodeFeatures)}')
    print(f'Edge features: {" ".join(edgeFeatures)}')

    metaData = {
        '': commonMetaData,
        'otext': oText,
        'oslots': dict(valueType='str'),
    }
    for ft in set(nodeFeatures) | set(edgeFeatures):
        metaData.setdefault(
            ft, {}
        )['valueType'] = 'int' if ft in numFeatures else 'str'
        if ft in specificMetaData:
            metaData[ft]['description'] = specificMetaData[ft]
    for ft in edgeFeaturesV:
        metaData[ft]['edgeValues'] = True

    print(f'Remove existing TF directory')
    rmtree(TF_DIR)
    print(f'Save TF dataset')
    TF = Fabric(locations=TF_DIR, silent=True)
    TF.save(
        nodeFeatures=nodeFeatures,
        edgeFeatures=edgeFeatures,
        metaData=metaData
    )


def loadTf():
    print(f'Load TF dataset for the first time')
    TF = Fabric(locations=TF_DIR, modules=[''])
    TF.clearCache()
    api = TF.load('')
    for (otp, av, omin, omax) in api.C.levels.data:
        print(f'{otp:<15}: {av:>7.4f} {{{omin:>6}-{omax:>6}}}')

    allFeatures = TF.explore(silent=False, show=True)
    loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
    TF.load(loadableFeatures)

    print('All done')


def main():
    if doParse:
        excavations = readMeta()
        tablets = parseCorpora(excavations)
        if errors:
            return
    if doTf:
        makeTf(tablets)
    if doLoad:
        loadTf()


main()
