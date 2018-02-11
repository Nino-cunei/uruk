import os
import collections
import re
import pprint
from glob import glob

REPO = 'nino-cunei'
ORIGIN = 'cdli'
REPO_DIR = os.path.expanduser(f'~/github/Dans-labs/{REPO}')
SOURCE_DIR = f'{REPO_DIR}/sources/{ORIGIN}'
TEMP_DIR = f'{REPO_DIR}/_temp'
EXPORT_FILE = f'{TEMP_DIR}/cldi_uruk.txt'

for cdir in (TEMP_DIR, ):
    os.makedirs(cdir, exist_ok=True)

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
    columm
    column3
'''.strip().split())

COMMENTS = set('''
    #
    $
'''.strip().split())

LOWER = set('abcdefghijklmnopqrstuvwxyz')
UPPER = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

CLUSTER_BEGIN = {'[': ']', '<': '>', '(': ')'}
CLUSTER_END = {y: x for (x, y) in CLUSTER_BEGIN.items()}

linePat = re.compile("([0-9a-zA-Z.'-]+)\s*(.*)")
numPartsPat = re.compile('([0-9-]+|[a-zA-Z]+)')

pp = pprint.PrettyPrinter(indent=2, width=100, compact=False)


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
    errors.setdefault(key, []).append('{}.{} ({}): {}'.format(
        p[0], p[1], curTablet.get('catalogId', ''), p[2]))


def diag(key, p, curTablet):
    diags.setdefault(key, []).append('{}.{} ({}): {}'.format(
        p[0], p[1], curTablet.get('catalogId', ''), p[2]))


def parseCorpora():
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
                        prevObject = curTablet.get('object', None)
                        newObject = (
                            ident if prevObject is None else
                            f'{prevObject}\\n{ident}'
                        )
                        curTablet['object'] = newObject
                elif kind == 'fragment':
                    if curTablet is None:
                        error('fragment outside tablet', p, curTablet or {})
                    else:
                        curFragment = ident
                else:
                    if kind in COLUMN:
                        if kind == 'columm':
                            diag(
                                'column typo: "@columm" => "@column"', p,
                                curTablet or {}
                            )
                        elif kind == 'column3':
                            diag(
                                'column typo: "column3" => "@column 3"', p,
                                curTablet or {}
                            )
                            ident = '3'
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
                                'srcLn': None,
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
                error('Cross reference without preceding line', p, curTablet or {})
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
                        f'{prevCrossref}\\n{crossref}'
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
                prevComment = target.get('comments', None)
                newComment = (
                    line if prevComment is None else f'{prevComment}\\n{line}'
                )
                target['comments'] = newComment
        else:
            if curColumn is None:
                diag(
                    f'Line outside column => inserted "@column 1"', p,
                    curTablet or {}
                )
                curColumn = {
                    'number': '1',
                    'lines': [],
                    'srcLn': None,
                    'srcLnNum': ln,
                }
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
                'number': lineNumber,
                'material': quads,
                'srcLn': line,
                'srcLnNum': ln,
            }
            if countPresent:
                curLine['countPresent'] = countPresent
            curColumn['lines'].append(curLine)
    corpora[prevCorpus]['to'] = len(tablets) - 1

    casify(tablets)
    fillup(tablets)

    printResults(corpora, tablets)
    printErrors(diags, diag=True)
    printErrors(errors)

    print('printing debug info')
    exportResults(tablets)
    print('done')


stripCommaPatFirst = re.compile('^\s*,\s*')
numeralEscapePat = re.compile('([0-9]+)\(([A-Za-z0-9~@]+)\)')


def numeralEscapeRepl(match):
    return f'«{match.group(1)}={match.group(2)}»'


def parseLine(material, p, curTablet):
    # transform the numerals
    material = stripCommaPatFirst.sub('', material)
    material = numeralEscapePat.sub(numeralEscapeRepl, material)
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
            if lq not in CLUSTER_END:
                stop = True
            else:
                lqo = CLUSTER_END[lq]
                start = startPoints.get(lqo, None)
                if start is None:
                    msg = 'Cluster ending in'
                    error(
                        f'{msg} {lq} misses {lqo} fq={fq} lq={lq}',
                        p,
                        curTablet or {},
                    )
                else:
                    clusters.append((lq, start, q))
                    del startPoints[lqo]
            if rest == '':
                stop = True
        newQuads.append(rest)
    if startPoints:
        error(
            f'Unterminated cluster(s): {sorted(startPoints.items())}', p,
            curTablet or {}
        )

    result = {'quads': newQuads}
    if clusters:
        result['clusters'] = clusters
    return result


def incNum(x):
    return str(int(x) + 1)


def casify(tablets):
    for tablet in tablets:
        for face in tablet.get('faces', []):
            for column in face.get('columns', []):
                lines = column.get('lines', None)
                if lines is not None:
                    column['cases'] = putInCases(lines)
                    del column['lines']


def putInCases(lines):
    cases = {}
    for line in lines:
        numParts = numPartsPat.findall(line['number'])
        if len(numParts):
            target = cases
            for numPart in numParts[0:-1]:
                target = target.setdefault(numPart, {})
            target[numParts[-1]] = line
        else:
            cases[''] = line
    return cases


def fillup(tablets):
    for tablet in tablets:
        faces = tablet.get('faces', None)
        if not faces:
            tablet['faces'] = [{'type': 'noface'}]
        faces = tablet['faces']
        for face in faces:
            columns = face.get('columns', None)
            if not columns:
                face['columns'] = [{'number': 0}]
            columns = face['columns']
            for column in columns:
                cases = column.get('cases', None)
                if not cases:
                    column['cases'] = {'': {'material': ''}}


def exportResults(tablets):
    with open(EXPORT_FILE, 'w') as fh:
        pq = pprint.PrettyPrinter(
            indent=2, width=100, compact=False, stream=fh
        )
        pq.pprint(tablets)


def printResults(corpora, tablets):
    limit = 2
    for (corpus, boundaries) in corpora.items():
        start = boundaries['from']
        end = boundaries['to']
        rest = 0
        if end > start + limit:
            end = start + limit
            rest = end - (start + limit)

        print(f'CORPUS {corpus} TABLETS {start}:{end}')
        for tabletData in tablets[start:end]:
            print(f'TABLET {tabletData["catalogId"]}')
            pp.pprint(tabletData)
        if rest:
            print(f'AND {rest} TABLETS MORE')


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


parseCorpora()
