import os
from glob import glob

LIMIT = 20


class Compare(object):
    def __init__(self, api, sourceDir, tempDir):
        self.api = api
        self.sourceDir = sourceDir
        self.tempDir = tempDir
        os.makedirs(tempDir, exist_ok=True)

    def strFromSign(self, n):
        F = self.api.F
        grapheme = F.grapheme.v(n)
        prime = "'" if F.prime.v(n) else ''

        variantValue = F.variant.v(n)
        variant = f'~{variantValue}' if variantValue else ''

        modifierValue = F.modifier.v(n)
        modifier = f'@{modifierValue}' if modifierValue else ''
        rmodifierValue = F.rmodifier.v(n)
        rmodifier = f'@{rmodifierValue}' if rmodifierValue else ''

        fullGrapheme = f'{grapheme}{prime}{variant}{rmodifier}'

        repeat = F.repeat.v(n)
        result = (
            f'{fullGrapheme}'
            if repeat is None else f'{repeat}({fullGrapheme})'
        )
        result = f'{result}{modifier}'

        return result

    def writeFreqs(self, fileName, data, dataName):
        print(f'There are {len(data)} {dataName}s')

        for (sortName, sortKey) in (
            ('alpha', lambda x: (x[0], -x[1])),
            ('freq', lambda x: (-x[1], x[0])),
        ):
            with open(f'{self.tempDir}/{fileName}-{sortName}.txt', 'w') as fh:
                for (item, freq) in sorted(data, key=sortKey):
                    if item != '':
                        fh.write(f'{freq:>5} x {item}\n')

    def readCorpora(self):
        files = glob(f'{self.sourceDir}/*.txt')
        tablets = set()
        for f in files:
            skipTablet = False
            curTablet = ''
            (dirF, fileF) = os.path.split(f)
            (corpus, ext) = os.path.splitext(fileF)
            with open(f) as fh:
                for (ln, line) in enumerate(fh):
                    line = line.rstrip('\n')
                    if len(line) and line[0] == '&':
                        comps = line[1:].split('=', 1)
                        curTablet = comps[0].strip()
                        if curTablet in tablets:
                            skipTablet = True
                        else:
                            skipTablet = False
                        tablets.add(curTablet)
                        yield (corpus, curTablet, ln + 1, line, skipTablet)
                    elif not skipTablet:
                        yield (corpus, curTablet, ln + 1, line, False)

    def checkSanity(self, headers, grepFunc, tfFunc):
        resultTf = tuple(tfFunc())
        resultGrep = tuple(grepFunc(self.readCorpora()))

        resultHeaders = '''
            period
            tablet
            ln
        '''.strip().split()
        resultHeaders.extend(headers)
        print(self._resultItem('HEAD', resultHeaders))

        firstDiff = -1
        lTf = len(resultTf)
        lGrep = len(resultGrep)
        minimum = min((lTf, lGrep))
        maximum = max((lTf, lGrep))
        equal = True
        n = 0
        while n < minimum:
            if resultTf[n] != resultGrep[n]:
                equal = False
                break
            n += 1
        if equal and minimum == maximum:
            print(f'IDENTICAL: all {maximum} items')
            self._printResult('=', resultTf)
        else:
            firstDiff = n
            print(
                'DIFFERENT: first different item is at position'
                f' {firstDiff + 1} in the list'
            )
            if firstDiff:
                self._printResult('=', resultTf[0:firstDiff], last=True)

            self._printResultLine('TF', resultTf, firstDiff)
            self._printResultLine('GREP', resultGrep, firstDiff)

            if firstDiff >= maximum - 1:
                print('\tno more items')
            else:
                print(
                    f'remaining items (TF: {lTf - firstDiff - 1});'
                    f' GREP: {lGrep - firstDiff - 1}'
                )
                for k in range(firstDiff + 1, firstDiff + LIMIT):
                    if k >= maximum:
                        print(f'{"":<5} no more items')
                        break
                    if k < lTf and k < lGrep and resultTf[k] == resultGrep[k]:
                        self._printResultLine('=', resultTf, k)
                    else:
                        self._printResultLine('TF', resultTf, k)
                        self._printResultLine('GREP', resultGrep, k)
                if k < maximum - 1:
                    print(f'{"TF":<5} and {lTf - k} more')
                    print(f'{"GREP":<5} and {lGrep - k} more')
        print(f'Number of results: TF {len(resultTf)}; GREP {len(resultGrep)}')

    def _printResult(self, prefix, result, last=False):
        if last:
            if len(result) > LIMIT:
                print(f'{prefix:<5} start with {len(result) - LIMIT} items')
            print(
                '\n'.join(
                    self._resultItem(prefix, r) for r in result[-LIMIT:]
                )
            )
        else:
            print(
                '\n'.join(
                    self._resultItem(prefix, r) for r in result[0:LIMIT]
                )
            )
            if len(result) > LIMIT:
                print(f'{prefix:<5} and {len(result) - LIMIT} more')
            else:
                print(f'{prefix:<5} no more items')

    def _printResultLine(self, prefix, result, ln):
        if ln >= len(result):
            print(f'{prefix:<5}: no line present')
        else:
            print(self._resultItem(prefix, result[ln]))

    def _resultItem(self, prefix, result):
        return f'{prefix:<5}: {" ◆ ".join(str(r) for r in result)}'
