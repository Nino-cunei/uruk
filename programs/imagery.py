import sys
import os
from subprocess import run
from shutil import rmtree

help = '''
python3 imagery command

commands:

    tablets: transforms tablet lineart eps to pdf
    ideographs: transforms ideograph lineart from eps to pdf

'''

REPO_DIR = os.path.expanduser('~/github/Dans-labs/Nino-cunei')
TABLET_FROM = f'{REPO_DIR}/_downloads/cdli_epstextcopies'
TABLET_TO = f'{REPO_DIR}/sources/cdli/images/tablets/lineart'
TABLET_COMMAND = '/usr/local/bin/ps2pdf'
TABLET_OPTIONS_IN = ['-dEPSCrop']
TABLET_OPTIONS_OUT = []
TABLET_EXT = ('eps', 'pdf')

IDEO_FROM = f'{REPO_DIR}/_downloads/archsignfiles_jpg'
IDEO_TO = f'{REPO_DIR}/sources/cdli/images/ideographs/lineart'
IDEO_COMMAND = '/usr/local/bin/magick'
IDEO_OPTIONS_IN = []
IDEO_OPTIONS_OUT = ['-trim', '+repage']
IDEO_EXT = ('jpg', 'jpg')


def doImages(
    fromDir, toDir, shellCommand, optionsIn, optionsOut, command, extIn, extOut
):
    if os.path.exists(toDir):
        rmtree(toDir)
    os.makedirs(toDir, exist_ok=True)
    seen = {}
    items = []
    duplicates = set()
    for (dirPath, dirNames, fileNames) in os.walk(fromDir):
        for fileName in fileNames:
            (base, ext) = os.path.splitext(fileName)
            ext = ext.lstrip('.')
            if ext != extIn:
                continue
            if fileName in seen:
                duplicates.add(fileName)
                print(
                    f'Duplicate file {fileName} in {dirPath}'
                    f' and {seen[fileName]}'
                )
                continue
            seen[fileName] = dirPath
            items.append(
                (base, f'{dirPath}/{fileName}', f'{toDir}/{base}.{extOut}')
            )
    if duplicates:
        print('Abort due to duplicates')
        return
    print(f'{len(items)} images to convert')

    for (i, (base, fromFile, toFile)) in enumerate(items):
        sys.stderr.write(f'{i+1:>5} {base:<30}\r')
        run([shellCommand] + optionsIn + [fromFile] + optionsOut + [toFile])


if len(sys.argv) <= 1:
    print(help)
command = sys.argv[1]
if command == 'tablets':
    doImages(
        TABLET_FROM, TABLET_TO, TABLET_COMMAND, TABLET_OPTIONS_IN,
        TABLET_OPTIONS_OUT, command, *TABLET_EXT
    )
elif command == 'ideographs':
    doImages(
        IDEO_FROM, IDEO_TO, IDEO_COMMAND, IDEO_OPTIONS_IN, IDEO_OPTIONS_OUT,
        command, *IDEO_EXT
    )
else:
    print(help)
