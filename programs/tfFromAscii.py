import os
import collections
import pprint
from glob import glob

REPO = 'nino-cunei'
ORIGIN = 'cdli'
REPO_DIR = os.path.expanduser(f'~/github/Dans-labs/{REPO}')
SOURCE_DIR = f'{REPO_DIR}/sources/{ORIGIN}'

FACES = set('''
    obverse
    reverse
    surface
    top
    bottom
    left
'''.strip().split())

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
    errors = {}
    prevCorpus = None

    def error(key, p):
        errors.setdefault(key, []).append('{}.{}: {}'.format(*p))

    for p in readCorpora():
        (corpus, ln, line) = p
        if corpus != prevCorpus:
            curTablet = None
            curFace = None
            if prevCorpus is not None:
                corpora[prevCorpus]['to'] = len(tablets)
            corpora[corpus] = {'from': len(tablets)}
        prevCorpus = corpus
        if len(line) == 0:
            continue
        fc = line[0]
        if fc == '&':
            comps = line[1:].split('=', 1)
            if len(comps) == 1:
                error('tablet name malformed', p)
                tNum = f'{corpus}.{ln}'
                tName = tNum
            else:
                tNum = comps[0].strip()
                tName = comps[1].strip()
            if tNum in tabletIndex:
                prevLn = tablets[tabletIndex[tNum]]['srcLn']
                error(f'tablet number duplicate, see line {prevLn}', p)
            curTablet = {
                'num': tNum,
                'name': tName,
                'faces': [],
                'corpus': corpus,
                'srcLn': ln,
            }
            curFace = None
            tabletIndex[tNum] = len(tablets)
            tablets.append(curTablet)
        elif fc == '@':
            kind = line[1:].strip()
            if kind == 'tablet':
                pass
            elif kind in FACES:
                if curTablet is None:
                    error('face outside tablet', p)
                else:
                    curFace = kind
                    curTablet[curFace] = {
                        'columns': [],
                        'srcLn': ln,
                    }
            else:
                comps = kind.split()
                if comps[0] == 'column':
                    colNum = comps[1] if len(comps) > 1 else '1'
                    if curFace is None:
                        error('column outside face', p)
                    else:
                        curTablet[curFace]['columns'].append({
                            'num': colNum,
                            'lines': [],
                            'srcLn': ln,
                        })
                else:
                    error(f'Face unknown: "{kind}"', p)
    corpora[prevCorpus]['to'] = len(tablets) - 1

    printResults(corpora, tablets)
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
            print(f'TABLET {tabletData["num"]}')
            pp.pprint(tabletData)
        if rest:
            print(f'AND {rest} TABLETS MORE')


def printErrors(errors):
    limit = 5
    if not errors:
        print('OK, no errors')
    else:
        for (key, ps) in sorted(
            errors.items(), key=lambda x: (-len(x[1]), x[0])
        ):
            print(f'Error {key} ({len(ps)}x)')
            for p in ps[0:limit]:
                print(f'\t{p}')
            if limit < len(ps):
                print(f'\tand {len(ps) - limit} more')


parseCorpora()
