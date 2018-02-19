import os
import re
from glob import glob


class Compare(object):
    def __init__(self, sourceDir, tempDir):
        self.sourceDir = sourceDir
        self.tempDir = tempDir
        os.makedirs(tempDir, exist_ok=True)

    def writeFreqs(self, fileName, data, dataName):
        print(f'There are {len(data)} {dataName}s')

        for (sortName, sortKey) in (
            ('alpha', lambda x: (x[0], -x[1])),
            ('freq', lambda x: (-x[1], x[0])),
        ):
            with open(
                f'{self.tempDir}/{fileName}-{sortName}.txt', 'w'
            ) as fh:
                for (item, freq) in sorted(
                    data, key=sortKey
                ):
                    if item != '':
                        fh.write(f'{freq:>5} x {item}\n')

    def readCorpora(self):
        files = glob(f'{self.sourceDir}/*.txt')
        nLines = 0
        for f in files:
            (dirF, fileF) = os.path.split(f)
            (corpus, ext) = os.path.splitext(fileF)
            with open(f) as fh:
                for (ln, line) in enumerate(fh):
                    nLines += 1
                    yield (corpus, ln + 1, line.rstrip('\n'))

    def checkSanity(self, grepPat, tfFunc):
        resultTf = list(tfFunc())
        pat = re.compile(grepPat)
        resultGrep = [
            f'{corpus} {ln}: {line}'
            for (corpus, ln, line) in self.readCorpora() if pat.match(line)
        ]

        print(f'Number of results: TF {len(resultTf)}; GREP {len(resultGrep)}')
        textTf = '\n'.join(resultTf)
        textGrep = '\n'.join(resultGrep)
        if textTf == textGrep:
            print('IDENTICAL')
            self._printResult(resultTf)
        else:
            print('DIFFERENT')
            print('----\nTF\n----\n')
            self._printResult(resultTf)
            print('----\nGREP\n----\n')
            self._printResult(resultGrep)

    def _printResult(self, result):
        LIMIT = 20
        print('\n'.join(result[0:LIMIT]))
        if len(result) > LIMIT:
            print('\t and {len(result) - LIMIT} more')
