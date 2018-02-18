import os
import re
from glob import glob


class Compare(object):
    def __init__(self, sourceDir):
        self.sourceDir = sourceDir

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
