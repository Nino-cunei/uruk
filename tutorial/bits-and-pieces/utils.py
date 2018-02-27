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


class Compare(object):
    def __init__(self, api, sourceDir, tempDir):
        self.api = api
        self.sourceDir = sourceDir
        self.tempDir = tempDir
        os.makedirs(tempDir, exist_ok=True)

    def strFromSign(self, n, flags=False):
        F = self.api.F
        Fs = self.api.Fs
        grapheme = F.grapheme.v(n)
        if grapheme == '…':
            grapheme = '...'
        prime = "'" if F.prime.v(n) else ''

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

    def strFromQuad(self, n, flags=False, outer=True):
        api = self.api
        E = api.E
        F = api.F
        Fs = api.Fs
        children = E.sub.f(n)
        if not children or len(children) < 2:
            return f'quad with less than two sub-quads should not happen'
        result = ''
        for child in children:
            nextChildren = E.op.f(child)
            if nextChildren:
                op = nextChildren[0][1]
            else:
                op = ''
            childType = F.otype.v(child)

            thisResult = (
                self.strFromQuad(child, flags=flags, outer=False) if
                childType == 'quad' else self.strFromSign(child, flags=flags)
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

    def strFromCluster(self, n, seen=None):
        api = self.api
        F = api.F
        E = api.E
        kind = F.kind.v(n)
        (bOpen, bClose) = CLUSTER_BRACKETS[kind]
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
                self.strFromCluster(child, seen=seen) if childType == 'cluster'
                else self.strFromQuad(child, flags=True) if childType == 'quad'
                else self.strFromSign(child, flags=True)
                if childType == 'sign' else None
            )
            seen.add(child)
            if thisResult is None:
                print(
                    f'TF: child of cluster has type {childType}:'
                    ' should not happen'
                )
            result.append(thisResult)
        return f'{bOpen}{" ".join(result)}{bClose}'

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