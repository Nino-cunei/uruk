import os
from glob import glob

LIMIT = 20

FLAGS = (
    ('damage', '#'),
    ('remarkable', '!'),
    ('written', ('!(', ')')),
    ('uncertain', '?'),
)

CLUSTER_BEGIN = {'[': ']', '<': '>', '(': ')'}
CLUSTER_END = {y: x for (x, y) in CLUSTER_BEGIN.items()}
CLUSTER_KIND = {'[': 'uncertain', '(': 'properName', '<': 'supplied'}
CLUSTER_BRACKETS = dict((name, (bOpen, CLUSTER_BEGIN[bOpen]))
                        for (bOpen, name) in CLUSTER_KIND.items())
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


class Compare(object):
    def __init__(self, cunei):
        self.api = cunei.api
        self.sourceDir = f'{cunei.sourceDir}/transcriptions/{cunei.version}'
        self.tempDir = cunei.tempDir

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
                        if curTablet in tablets or curTablet in BLACKLIST:
                            skipTablet = True
                        else:
                            skipTablet = False
                        tablets.add(curTablet)
                        yield (corpus, curTablet, ln + 1, line, skipTablet)
                    elif not skipTablet:
                        yield (corpus, curTablet, ln + 1, line, False)

    def checkSanity(self, headers, grepFunc, tfFunc, leeway=0):
        def equalLeeway(tfTuple, grepTuple):
            if not leeway:
                return tfTuple == grepTuple

            tfRest = tfTuple[0:2] + tfTuple[3:]
            grepRest = grepTuple[0:2] + grepTuple[3:]
            tfLn = tfTuple[2]
            grepLn = grepTuple[2]
            theDiff = abs(grepLn - tfLn)
            if theDiff > leeway:
                return False
            else:
                return tfRest == grepRest

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
            if not equalLeeway(resultTf[n], resultGrep[n]):
                equal = False
                break
            n += 1
        good = False
        if equal and minimum == maximum:
            print(f'IDENTICAL: all {maximum} items')
            self._printResult('=', resultTf)
            good = True
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
        return good

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
