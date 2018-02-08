import os
import sys
import re
from glob import glob

REPO = 'nino-cunei'
ORIGIN = 'cdli'
REPO_DIR = os.path.expanduser(f'~/github/Dans-labs/{REPO}')
SOURCE_DIR = f'{REPO_DIR}/sources/{ORIGIN}'

FACES = set('''
    obverse
    reverse
'''.strip().split())

def readCorpora():
    lines = []
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
    corpora = {}
    thisCorpus = None
    thisTablet = None
    errors = {}

    def error(key, p):
        errors.setdefault(key, []).append('{}.{}: {}'.format(*p))

    for p in readCorpora():
        (corpus, ln, line) = p
        if corpus not in corpora:
            thisCorpus = {}
            corpora[corpus] = thisCorpus
            thisTablet = None
            thisFace = None
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
            if tNum in thisCorpus:
                prevLn = thisCorpus[tNum]['ln']
                error(
                    f'tablet number duplicate, see line {prevLn}',
                    p
                )
            tabletData = {
                'name': tName,
                'faces': {},
                'ln': ln,
            }
            thisCorpus[tNum] = tabletData
            thisTablet = tabletData['faces']
            thisFace = None
        elif fc == '@':
            kind = line[1:].strip()
            if kind == 'tablet':
                pass
            elif kind in FACES:
                if thisCorpus is None:
                    error('face outside tablet', p)
                else:
                    thisTablet[kind] = {'columns': []}
                    thisFace = kind
            else:
                comps = kind.split()
                if comps[0] == 'column':
                    colNum = comps[1] if len(comps) > 1 else '1'
                    if thisFace is None:
                        error('column outside face', p)
                    else:
                        thisTablet[thisFace]['columns'].append({'num': colNum})
                else:
                    error(f'Face unknown: "{kind}"', p)

    printResults(corpora)
    printErrors(errors)


def printResults(corpora):
    limit = 10
    for (corpus, corpusData) in corpora.items():
        print(f'Corpus {corpus} ({len(corpusData)} tablets)')
        for (i, (tNum, tabletData)) in enumerate(corpusData.items()):
            if i >= limit - 1:
                break
            print(f'\t{tNum} = {tabletData["name"]}')
        if limit < len(corpusData):
            print(f'\tand {len(corpusData) - limit} more')


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
