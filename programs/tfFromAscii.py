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

REPO = 'nino-cunei'
ORIGIN = 'cdli'
REPO_DIR = os.path.expanduser(f'~/github/Dans-labs/{REPO}')
SOURCE_DIR = f'{REPO_DIR}/sources/{ORIGIN}'
TEMP_DIR = f'{REPO_DIR}/_temp'
EXPORT_FILE = f'{TEMP_DIR}/cldi_uruk.txt'

# -1 is unlimited

LIMIT = -1

SHOWCASES = set(
    '''
    P000743
    P000736
    P002113
    P004639
    P006275
    P006284
    P006427
    P006437
    P325218
    P411604
    P411610
    P448701
    P464118
    P499393
'''.strip().split()
)

CORPUS = 'uruk'
VERSION = '0.1'
TF_DIR = f'{REPO_DIR}/tf/{CORPUS}/{VERSION}'

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
    catalogId=(
        'identifier of tablet in catalog'
        ' (http://www.flutopedia.com/tablets.htm)'
    ),
    name='name of tablet',
    period='period indication of tablet',
    srcLn='transcribed line',
    srcLnNum='line number in transcription file',
    type='type of a face',
    number='number of a column or line',
    grapheme='name of a grapheme (glyph)',
    variant='corresponds to ~x in transcription',
    uncertain='corresponds to ?-flag in transcription',
    damage='corresponds to #-flag in transcription',
    modifier='corresponds to @x in transcription',
    identifier='additional information pertaining to the name of a face',
    remarkable='corresponds to ! flag in transcription ',
    written='corresponds to !(xxx) flag in transcription',
    prime='indicates the presence of a prime (single quote)',
    fragment='level between tablet and face',
    repeat=(
        'number indicating the number of repeats of a grapheme,'
        'especially in numerals'
    ),
    op='operator connecting left to right operand',
    sub='connects line or case with subcases, or quad with sub-quads or signs',
)
numFeatures = set(
    '''
    srcLnNum
    uncertain
    damage
    remarkable
    prime
    repeat
'''.strip().split()
)

oText = {
    'levels': 'tablet,face,column,line,case,cluster,quad,comment,sign',
    'sectionFeatures': 'catalogId,number,number',
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
CLUSTER_TYPE = {'[': 'uncertain', '(': 'properName', '<': 'supplied'}

OPERATORS = set('''
    x
    %
    &
    .
    :
    +
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
    ('@columm', '@column', 'Typo in column specifier: @columm'),
    ('@column3', '@column 3', 'Typo in column specifier: @column 3'),
)

TWEAK_MATERIAL = (
    ('4"', "4'", 'Strange double prime'),
    ('[,', '', 'Strange comma'),
    ('SA|L', 'SAL|', 'Inversion "SA|L"'),
    ('~x(', '~x (', 'Juxtaposed quads'),
    (')|U', ') |U', 'Juxtaposed quads'),
    ('1N(02)', '1(N02)', 'N outside brackets'),
    ('(1N', '1(N', 'repeat inside brackets'),
    ('~A', '~a', 'variant with capital letter: ~A'),
    ('{', '(', 'wrong opening bracket {'),
    ('}', ')', 'wrong closing bracket {'),
)
TWEAK_LINES = (
    ('1.a1. 4(N14)# , |4', '1.b0. 4(N14)# , |4', 'wrong line number'),
    ('1.a2. UB', '1.c2. UB', 'wrong line number'),
)

linePat = re.compile("([0-9a-zA-Z.'-]+)\s*(.*)")
numPartsPat = re.compile('([0-9-]+|[a-zA-Z]+)')

stripCommas = re.compile('\s*,\s*')
repeatEscapePat = re.compile("([0-9]+)\(([A-Za-z0-9@'~]+)\)")
repeatPat = re.compile('^«([^=]*)=([^»]*)»$')

fragEscapePat = re.compile('\.\.\.')

writtenEscapePat = re.compile('!\(([^)]*)\)')
writtenRestorePat = re.compile('!◀([^▶]*)▶')

flagsPat = re.compile('^(.*)((?:!◀[^▶]*▶)|[!#?*])$')
modifierPat = re.compile('^(.*)@(.)$')
variantPat = re.compile('^(.*)~([a-wyz0-9]+)$')

operatorPat = re.compile(f'[{"".join(OPERATORS)}]')

pp = pprint.PrettyPrinter(indent=2, width=100, compact=False)

for cdir in (TEMP_DIR, TF_DIR):
    os.makedirs(cdir, exist_ok=True)


def readCorpora():
    files = glob(f'{SOURCE_DIR}/*.txt')
    nLines = 0
    for f in files:
        (dirF, fileF) = os.path.split(f)
        (corpus, ext) = os.path.splitext(fileF)
        print(f'Corpus "{corpus}" ...')
        with open(f) as fh:
            for (ln, line) in enumerate(fh):
                nLines += 1
                yield (corpus, ln + 1, line.rstrip('\n'))
        print(f'\t{nLines:>7} lines')


errors = {}
diags = {}


def error(key, p, curTablet):
    errors.setdefault(key, []).append(
        '{}.{} ({}): {}'.format(
            p[0], p[1], curTablet.get('catalogId', ''), p[2]
        )
    )


def diag(key, p, curTablet):
    diags.setdefault(key, []).append(
        '{}.{} ({}): {}'.format(
            p[0], p[1], curTablet.get('catalogId', ''), p[2]
        )
    )


def parseCorpora(export=False):
    corpora = collections.OrderedDict()
    tablets = []
    tabletIndex = {}
    curTablet = None
    curFace = None
    curFragment = None
    curColumn = None
    curNums = None
    curLine = None
    prevNum = None
    skipTablet = False
    prevCorpus = None

    for p in readCorpora():
        (corpus, ln, line) = p
        if corpus != prevCorpus:
            curTablet = None
            curFace = None
            curColumn = None
            curNums = None
            curLine = None
            prevNum = None
            if prevCorpus is not None:
                corpora[prevCorpus]['to'] = len(tablets)
            corpora[corpus] = {'from': len(tablets)}
        prevCorpus = corpus
        if len(line) == 0:
            continue
        fc = line[0]
        if len(line) == 1:
            if fc != ' ':
                error('Single character line', p, curTablet or {})
            continue
        if fc in HEAD_CHARS:
            for (pat, rep, msg) in TWEAK_HEADS:
                if line.startswith(pat):
                    diag(msg, p, curTablet)
                    line = line.replace(pat, rep)
        sc = line[1]
        if fc == '&':
            comps = line[1:].split('=', 1)
            skipTablet = False
            if len(comps) == 1:
                error('tablet name malformed', p, curTablet or {})
                tNum = f'{corpus}.{ln}'
                tName = tNum
            else:
                tNum = comps[0].strip()
                tName = comps[1].strip()
            if tNum in tabletIndex:
                prevLn = tablets[tabletIndex[tNum]]['srcLn']
                msg = 'skipped latter one'
                diag(
                    f'tablet number duplicate, see line {prevLn} => {msg}', p,
                    curTablet or {}
                )
                skipTablet = True
            else:
                if len(tablets) == LIMIT:
                    break
                curTablet = {
                    'catalogId': tNum,
                    'name': tName,
                    'faces': [],
                    'period': corpus,
                    'srcLn': line,
                    'srcLnNum': ln,
                }
                curFragment = None
                curFace = None
                curColumn = None
                curNums = None
                curLine = None
                prevNum = None
                tabletIndex[tNum] = len(tablets)
                tablets.append(curTablet)
        elif fc == '@':
            if skipTablet:
                continue
            kind = line[1:].strip()
            if kind == 'tablet':
                pass
            else:
                comps = kind.split(maxsplit=1)
                kind = comps[0]
                ident = comps[1] if len(comps) > 1 else None
                if kind in FACES:
                    if curTablet is None:
                        error('face outside tablet', p, curTablet or {})
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
                        error('object outside tablet', p, curTablet or {})
                    elif curFace is not None:
                        error('object within face', p, curTablet or {})
                    else:
                        curTablet.setdefault('comments', []).append({
                            'srcLn': line,
                            'srcLnNum': ln,
                        })
                elif kind == 'fragment':
                    if curTablet is None:
                        error('fragment outside tablet', p, curTablet or {})
                    else:
                        curFragment = ident
                else:
                    if kind in COLUMN:
                        colNum = '1' if ident is None else ident
                        countPresent = False
                        if "'" in colNum:
                            countPresent = True
                            colNum = colNum.replace("'", '')
                        if curFace is None:
                            diag(
                                'column outside face => inserted "@obverse"',
                                p, curTablet or {}
                            )
                            curFace = {
                                'type': 'obverse',
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
                            'lines': [],
                            'srcLn': line,
                            'srcLnNum': ln,
                        }
                        curNums = set()
                        curLine = None
                        prevNum = None
                        if countPresent:
                            curColumn['countPresent'] = countPresent
                        curFace['columns'].append(curColumn)
                    else:
                        error(f'Face unknown: "{kind}"', p, curTablet or {})
        elif fc == '>' and sc == '>':
            if curLine is None:
                error(
                    'Cross reference without preceding line', p, curTablet
                    or {}
                )
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
                    error('Malformed cross reference', p, curTablet or {})
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
            target = (
                curLine if curLine else curColumn if curColumn else curFace
                if curFace else curTablet
            )
            if target is None:
                error('Comment outside tablet', p, curTablet or {})
            else:
                target.setdefault('comments', []).append({
                    'srcLn': line,
                    'srcLnNum': ln,
                })
        else:
            # tweak
            for (pat, rep, msg) in TWEAK_LINES:
                if line.startswith(pat):
                    diag(msg, p, curTablet)
                    line = line.replace(pat, rep, 1)
            if curColumn is None:
                diag(
                    f'Line outside column => inserted "@column 0"', p,
                    curTablet or {}
                )
                curColumn = {
                    'number': '0',
                    'lines': [],
                    'srcLn': line,
                    'srcLnNum': ln,
                }
                curFace['columns'].append(curColumn)
                curNums = set()
                curLine = None
                prevNum = None
            match = linePat.match(line)
            if match is None:
                diag('Missing line number', p, curTablet or {})
                lineNumber = incNum(prevNum)
                prevNum = lineNumber
                material = line
            else:
                lineNumber = match.group(1).replace('.', '')
                prevNum = lineNumber
                material = match.group(2).strip()
            countPresent = False
            if "'" in lineNumber:
                countPresent = True
                lineNumber = lineNumber.replace("'", '')
            if lineNumber in curNums:
                error(
                    f'Duplicate line number "{lineNumber}" in column', p,
                    curTablet or {}
                )
            if fc in LOWER:
                diag('Line number starting with a-z', p, curTablet or {})
            elif fc in UPPER:
                diag('Line number starting with A-Z', p, curTablet or {})
            quads = parseLine(material, p, curTablet)
            curLine = {
                'fullNumber': lineNumber,
                'material': quads,
                'srcLn': line,
                'srcLnNum': ln,
            }
            if countPresent:
                curLine['countPresent'] = countPresent
            curColumn['lines'].append(curLine)
    corpora[prevCorpus]['to'] = len(tablets) - 1

    casify(tablets)

    print(f'Parsed {len(tablets)} tablets')

    printErrors(diags, diag=True)
    printErrors(errors)

    if export:
        exportResults(tablets)
        print('Showcases written to file')
    return tablets


def repeatEscapeRepl(match):
    return f'«{match.group(1)}={match.group(2)}»'


def writtenEscapeRepl(match):
    return f'!◀{match.group(1)}▶'


def parseLine(material, p, curTablet):
    # tweak
    for (pat, rep, msg) in TWEAK_MATERIAL:
        if pat in material:
            diag(msg, p, curTablet)
            material = material.replace(pat, rep)
    # remove the commas and transform the numerals
    material = stripCommas.sub(' ', material)
    material = repeatEscapePat.sub(repeatEscapeRepl, material)
    material = writtenEscapePat.sub(writtenEscapeRepl, material)
    # translate ... to …
    material = fragEscapePat.sub('…', material)
    quads = material.split()
    startPoints = {}
    clusters = []
    newQuads = []
    for (q, quad) in enumerate(quads):
        stop = False
        rest = quad

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
                cType = CLUSTER_TYPE[lqo]
                start = startPoints.get(lqo, None)
                if start is None:
                    msg = 'Cluster ending in'
                    error(
                        f'{msg} {lq} misses {lqo} fq={fq} lq={lq}',
                        p,
                        curTablet or {},
                    )
                else:
                    clusters.append((cType, start, q))
                    del startPoints[lqo]
            if rest == '':
                stop = True
        # (rest, quadInfo) = getPieceInfo(rest, p, curTablet)
        # newQuad = parseQuad(rest, p, curTablet)
        # if quadInfo:
        #    newQuad.setdefault('info', {}).update(quadInfo)
        quadInfo = {}
        if rest.startswith('|'):
            (rest, quadInfo) = getPieceInfo(rest, p, curTablet)
        newQuad = parseQuad(rest, p, curTablet)
        if quadInfo:
            newQuad.setdefault('info', {}).update(quadInfo)
        newQuads.append(newQuad)
    if startPoints:
        error(
            f'Unterminated cluster(s): {sorted(startPoints.items())}', p,
            curTablet or {}
        )

    result = {'quads': newQuads}
    if clusters:
        result['clusters'] = clusters
    return result


def getPieceInfo(piece, p, curTablet, empty_ok=False):
    base = piece
    pieceInfo = dict()

    stop = False
    while base != '' and not stop:
        # flags
        splits = flagsPat.findall(base)
        if splits:
            items = pieceInfo.setdefault('flags', {})
            (base, itemStr) = splits[0]
            if itemStr == '#':
                if 'damage' in items:
                    error(f'Flag "#" repeated', p, curTablet)
                items['damage'] = 1
            elif itemStr == '?':
                if 'uncertain' in items:
                    error(f'Flag "?" repeated', p, curTablet)
                items['uncertain'] = 1
            elif itemStr.startswith('!'):
                if 'remarkable' in items:
                    error(f'Flag "!" repeated', p, curTablet)
                items['remarkable'] = 1
                if len(itemStr) > 1:
                    if 'written' in items:
                        error(f'Flag "!()" repeated', p, curTablet)
                    items['written'] = itemStr[2:-1]
            continue

        # modifiers
        splits = modifierPat.findall(base)
        if splits:
            items = pieceInfo.setdefault('modifiers', set())
            (base, itemStr) = splits[0]
            if itemStr not in MODIFIERS:
                error(f'Modifier "@{itemStr}" unknown', p, curTablet)
            else:
                if itemStr in items:
                    error(f'Modifier "@{itemStr}" repeated', p, curTablet)
                items.add(itemStr)
            continue

        # variants
        splits = variantPat.findall(base)
        if splits:
            items = pieceInfo.setdefault('variants', set())
            (base, itemStr) = splits[0]
            if itemStr in items:
                diag(f'Variant "~{itemStr}" repeated', p, curTablet)
            items.add(itemStr)
            continue

        # primes
        if base != '' and base[-1] == "'":
            base = base[0:-1]
            if 'prime' in pieceInfo:
                error(f'Prime repeated', p, curTablet)
            pieceInfo['prime'] = 1
            continue

        stop = True

    if not empty_ok:
        if base == '':
            error(f'Empty grapheme', p, curTablet)
    return (base, pieceInfo)


def parseQuad(quad, p, curTablet):
    base = quad
    if base != '':
        if base[0] == '|':
            if len(base) == 1:
                error('Empty quad "|"', p, curTablet)
                base = ''
            else:
                if base[-1] == '|':
                    if len(base) == 2:
                        error('Empty quad "||"', p, curTablet)
                        base = ''
                    else:
                        base = base[1:-1]
                else:
                    error('Quad not terminated with "|"', p, curTablet)
                    base = base[1:]
        else:
            if base[-1] == '|':
                diag('Quad does not start with "|"', p, curTablet)
                base = base[0:-1]
    struct = quadStructure(base, p, curTablet)
    return struct


def parseTerminal(string):
    return [] if string == '' else [string]


def parseBrackets(string, fromPos, wantClose):
    result = []
    errors = []
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
                errors.append(f'Extra ")" in "{pb}▶{pB}◀{pa}"')
            fromPos = firstBracket + 1
        elif bracket == '(':
            (subResult, fromPos, subErrors) = parseBrackets(
                string,
                firstBracket + 1,
                True,
            )
            result.append(subResult)
            errors.extend(subErrors)
        else:
            fromPos = ls
    if wantClose:
        if fromPos >= ls:
            errors.append(f'Missing ")" after "{string}▲"')
        elif string[fromPos] != ')':
            errors.append(
                f'Missing ")" in "{string[0:fromPos]}▲{string[fromPos:]}"',
            )
        else:
            fromPos += 1
    return (result, fromPos, errors)


def quadStructure(string, p, curTablet):
    (result, restPos, errors) = parseBrackets(string, 0, False)
    if restPos < len(string):
        pb = string[0:restPos]
        pa = string[restPos:]
        errors.append(f'Trailing characters in "{pb}▲{pa}"')
    if errors:
        errorStr = '\n\t\t'.join(errors)
        error(f'bracket error in quad:\n\t\t{errorStr}', p, curTablet or {})
    return transformQuad(result, p, curTablet)


def transformQuad(quads, p, curTablet):
    dest = []
    for quad in quads:
        if type(quad) is str:
            ls = len(quad)
            signDatas = []
            k = 0
            signs = operatorPat.split(quad)
            for (g, sign) in enumerate(signs):
                (base, info) = getPieceInfo(
                    sign,
                    p,
                    curTablet,
                    empty_ok=True,
                )
                k += len(sign)
                operator = quad[k] if k < ls else ''
                k += 1
                rInfo = {}
                if g == 0 and base == '' and info:
                    dest[-1].setdefault('info', {}).update(info)
                else:
                    parts = repeatPat.findall(base)
                    signData = {}
                    if parts:
                        (n, base) = parts[0]
                        signData['repeat'] = n
                        (base, rInfo) = getPieceInfo(
                            base,
                            p,
                            curTablet,
                        )
                    if '«' in base or '»' in base:
                        error(
                            'Incomplete recognition of escaped repeats:'
                            f' "{sign}" => "{base}"', p, curTablet
                        )
                    signData['grapheme'] = base
                    info.update(rInfo)
                    if info:
                        signData['info'] = info
                    if operator != '':
                        signData['op'] = operator
                    signDatas.append(signData)

            if len(signDatas):
                if len(signDatas) == 1:
                    dest.append(signDatas[0])
                else:
                    dest.append({'quads': signDatas})
        else:
            subQuad = transformQuad(quad, p, curTablet)
            dest.append(subQuad)
    result = (dest[0] if len(dest) == 1 else {'quads': dest})
    return result


def incNum(x):
    return str(int(x) + 1)


def casify(tablets):
    for tablet in tablets:
        curTablet = tablet
        for face in tablet.get('faces', []):
            for column in face.get('columns', []):
                lines = column.get('lines', None)
                if lines is not None:
                    column['lines'] = putInCases(lines, curTablet)


def putInCases(lines, curTablet):
    cases = collections.OrderedDict()
    for line in lines:
        numParts = numPartsPat.findall(line['fullNumber'])
        if len(numParts):
            target = cases
            for numPart in numParts[0:-1]:
                reshapeTarget(target, curTablet)
                target = target.setdefault(numPart, collections.OrderedDict())
            lastPart = numParts[-1]
            reshapeTarget(target, curTablet)
            target[lastPart] = line
        else:
            cases[''] = line
    return cases


def reshapeTarget(target, curTablet):
    if 'material' in target:
        # this happens if you have a numbering like
        # 1  material 1
        # 1a material 1a
        # 1b material 1b
        srcLn = target['srcLnNum']
        srcLine = target['srcLn']
        period = curTablet.get('period', None)
        diag(
            'case with sub-cases has material', (period, srcLn, srcLine),
            curTablet
        )
        existing = {}
        existing.update(target)
        target.clear()
        target[''] = existing


def exportResults(tablets):
    with open(EXPORT_FILE, 'w') as fh:
        pq = pprint.PrettyPrinter(
            indent=2, width=100, compact=False, stream=fh
        )
        pq.pprint([
            tablet for tablet in tablets if tablet['catalogId'] in SHOWCASES
        ])


def printErrors(errors, diag=False):
    limit = 5
    ErrorStr = 'Diagnostic' if diag else 'Error'
    errorStr = 'diagnostic' if diag else 'error'
    errorsStr = f'{errorStr}s'
    if not errors:
        print(f'OK, no {errorsStr}')
    else:
        for (key, ps) in sorted(
            errors.items(), key=lambda x: (-len(x[1]), x[0])
        ):
            print(f'{ErrorStr} {key} ({len(ps)}x)')
            for p in ps[0:limit]:
                print(f'\t{p}')
            if limit < len(ps):
                print(f'\tand {len(ps) - limit} more')


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
            doCases(lineData, 'line', curNode)
            context.pop()

    def doCases(cases, parentType, parentNode):
        nodeType = 'case'
        if 'material' in cases:
            doCase(cases, parentType, parentNode)
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

    def doCase(case, parentType, parentNode):
        nodeType = 'case'
        cur[nodeType] += 1
        curNode = cur[nodeType]
        for ft in '''
            fullNumber
            srcLn
            srcLnNum
        '''.strip().split():
            if ft in case:
                nodeFeatures[ft][(nodeType, curNode)] = case[ft]
        if parentNode is not None:
            edgeFeatures['sub'][(parentType,
                                 parentNode)].add((nodeType, curNode))
        material = case.get('material', {})
        context.append((nodeType, curNode))
        doComments(case, 'case')
        hasQuads = doClusters(material)
        if not material or not hasQuads:
            doEmptySign()
        context.pop()

    def doComments(thing, thingType):
        nodeType = 'comment'
        for comment in thing.get('comments', []):
            cur[nodeType] += 1
            curNode = cur[nodeType]
            for ft in '''
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
        for (kind, fromQuad, toQuad) in clusters:
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
            prevQuad = quad
        q = len(quads)
        if q in endClusters:
            for kind in endClusters[q]:
                context.pop()
        return len(quads)

    def doQuad(q, quad, prevQuad, prevType, prevNode, parentType, parentNode):
        nodeType = 'quad'
        cur[nodeType] += 1
        curNode = cur[nodeType]
        if parentType is not None:
            edgeFeatures['sub'][(parentType,
                                 parentNode)].add((nodeType, curNode))
        if q > 1:
            op = prevQuad.get('op', None)
            if op is not None:
                edgeFeaturesV['op'][(prevType, prevNode)][(nodeType,
                                                           curNode)] = op
        context.append((nodeType, curNode))
        if 'quads' in quad:
            doInfo(quad, curNode, nodeType)
            (pQuad, pType, pNode) = (None, None, None)
            for (iq, iquad) in enumerate(quad['quads']):
                (pType, pNode) = doQuad(
                    iq, iquad, pQuad, pType, pNode, nodeType, curNode
                )
                pQuad = iquad
        if 'grapheme' in quad:
            doSign(quad)
        context.pop()
        return (nodeType, curNode)

    def doSign(sign):
        nonlocal curSlot
        nodeType = 'sign'
        curSlot += 1
        for ft in '''
            grapheme
            repeat
        '''.strip().split():
            if ft in sign:
                nodeFeatures[ft][(nodeType, curSlot)] = sign[ft]
        doInfo(sign, curSlot, nodeType)
        for (nt, curNode) in context:
            oSlots[(nt, curNode)].add(curSlot)

    def doEmptySign():
        doSign({'grapheme': ''})

    def doInfo(data, node, nodeType):
        infoData = data.get('info', {})
        if 'prime' in infoData:
            nodeFeatures['prime'][(nodeType, node)] = 1
        if 'variants' in infoData:
            nodeFeatures['variant'][(nodeType,
                                     node)] = ','.join(infoData['variants'])
        if 'flags' in infoData:
            for (flag, value) in infoData['flags'].items():
                nodeFeatures[flag][(nodeType, node)] = value
        if 'modifiers' in infoData:
            nodeFeatures['modifier'][(nodeType,
                                      node)] = ','.join(infoData['modifiers'])

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
    tablets = parseCorpora(export=True)
    if errors:
        return
    makeTf(tablets)
    loadTf()


main()
