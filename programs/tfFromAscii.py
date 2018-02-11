import os
import collections
import re
import pprint
from glob import glob

REPO = 'nino-cunei'
ORIGIN = 'cdli'
REPO_DIR = os.path.expanduser(f'~/github/Dans-labs/{REPO}')
SOURCE_DIR = f'{REPO_DIR}/sources/{ORIGIN}'

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

linePat = re.compile("([0-9a-zA-Z.'-]+)\s*(.*)")

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
                yield (corpus, ln, line.rstrip('\n'))
        print(f'\t{nLines:>7} lines')


def parseCorpora():
    corpora = collections.OrderedDict()
    tablets = []
    tabletIndex = {}
    curTablet = None
    curFace = None
    curFragment = None
    curColumn = None
    skipTablet = False
    errors = {}
    diags = {}
    prevCorpus = None

    def error(key, p):
        errors.setdefault(key, []).append('{}.{}: {}'.format(*p))

    def diag(key, p):
        diags.setdefault(key, []).append('{}.{}: {}'.format(*p))

    for p in readCorpora():
        (corpus, ln, line) = p
        if corpus != prevCorpus:
            curTablet = None
            curFace = None
            curColumn = None
            if prevCorpus is not None:
                corpora[prevCorpus]['to'] = len(tablets)
            corpora[corpus] = {'from': len(tablets)}
        prevCorpus = corpus
        if len(line) == 0:
            continue
        fc = line[0]
        if fc == '&':
            comps = line[1:].split('=', 1)
            skipTablet = False
            if len(comps) == 1:
                error('tablet name malformed', p)
                tNum = f'{corpus}.{ln}'
                tName = tNum
            else:
                tNum = comps[0].strip()
                tName = comps[1].strip()
            if tNum in tabletIndex:
                prevLn = tablets[tabletIndex[tNum]]['srcLn']
                msg = 'skipped latter one'
                diag(f'tablet number duplicate, see line {prevLn} => {msg}', p)
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
                        error('face outside tablet', p)
                    else:
                        face = {
                            'columns': [],
                            'srcLn': line,
                            'srcLnNum': ln,
                        }
                        if ident:
                            face['identifier'] = ident
                        if curFragment is not None:
                            face['fragment'] = curFragment
                        curFace = kind
                        curTablet[curFace] = face
                        curColumn = None
                elif kind == 'object':
                    if curTablet is None:
                        error('object outside tablet', p)
                    elif curFace is not None:
                        error('object within face', p)
                    else:
                        prevObject = curTablet.get('object', None)
                        newObject = (
                            ident if prevObject is None else
                            f'{prevObject}\\n{ident}'
                        )
                        curTablet['object'] = newObject
                elif kind == 'fragment':
                    if curTablet is None:
                        error('fragment outside tablet', p)
                    else:
                        curFragment = ident
                else:
                    if kind in COLUMN:
                        if kind == 'columm':
                            diag('column typo: "@columm" => "@column"', p)
                        elif kind == 'column3':
                            diag('column typo: "column3" => "@column 3"', p)
                            ident = '3'
                        colNum = '1' if ident is None else ident
                        countPresent = False
                        if "'" in colNum:
                            countPresent = True
                            colNum = colNum.replace("'", '')
                        if curFace is None:
                            diag(
                                'column outside face => inserted "@obverse"', p
                            )
                            face = {
                                'columns': [],
                                'srcLn': None,
                                'srcLnNum': ln,
                            }
                            curFace = 'obverse'
                            curTablet[curFace] = face
                        curColumn = {
                            'number': colNum,
                            'lines': [],
                            'srcLn': line,
                            'srcLnNum': ln,
                        }
                        if countPresent:
                            curColumn['countPresent'] = countPresent
                        curTablet[curFace]['columns'].append(curColumn)
                    else:
                        error(f'Face unknown: "{kind}"', p)
        elif fc.isdigit():
            if curColumn is None:
                diag(f'Line outside column => inserted "@column 1"', p)
                curColumn = {
                    'number': '1',
                    'lines': [],
                    'srcLn': None,
                    'srcLnNum': ln,
                }
            match = linePat.match(line)
            if match is None:
                error(f'Malformed line: "{line}"', p)
            else:
                lineNumber = match.group(1).replace('.', '')
                countPresent = False
                if "'" in lineNumber:
                    countPresent = True
                    lineNumber = lineNumber.replace("'", '')
                lineData = {
                    'number': lineNumber,
                    'material': match.group(2),
                    'srcLn': line,
                    'srcLnNum': ln,
                }
                if countPresent:
                    lineData['countPresent'] = countPresent
                curColumn['lines'].append(lineData)
    corpora[prevCorpus]['to'] = len(tablets) - 1

    printResults(corpora, tablets)
    printErrors(diags, diag=True)
    printErrors(errors)


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
