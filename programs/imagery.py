import sys
import os
import ssl
from glob import glob
from subprocess import run
from shutil import rmtree
from urllib.request import urlopen

help = '''
python3 imagery command

commands:

    tablets: transforms tablet lineart eps to pdf
    ideographs: transforms ideograph lineart from eps to pdf
    photos: decreases the size of the jpegs of the tablets
    scrape: scrape tablet photos from cdli

'''

SOURCE = 'uruk'
VERSION = '1.0'
REPO_DIR = os.path.expanduser(f'~/github/Nino-cunei/{SOURCE}')
CATALOG = f'{REPO_DIR}/tf/{SOURCE}/{VERSION}/catalogID.tf'
QUALITY = '30%'

CDLI_URL = 'https://cdli.ucla.edu/dl/photo'

PHOTO_FROM = f'{REPO_DIR}/_downloads/cdli_photos'
PHOTO_TO = f'{REPO_DIR}/sources/cdli/images/tablets/photos'
PHOTO_COMMAND = '/usr/local/bin/magick'
PHOTO_OPTIONS_IN = []
PHOTO_OPTIONS_OUT = ['-quality', QUALITY]
PHOTO_EXT = ('jpg', 'jpg')

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


def doScrape():
    catalog = set()
    os.makedirs(PHOTO_FROM, exist_ok=True)
    with open(CATALOG) as fh:
        for line in fh:
            line = line.rstrip('\n')
            if line == '' or line[0] == '@':
                continue
            comps = line.split('\t', maxsplit=1)
            pNum = comps[-1]
            catalog.add(pNum)
    print(f'{len(catalog):>4} tablets in corpus')
    existingFiles = glob(f'{PHOTO_FROM}/*.jpg')
    existing = set()
    for filePath in existingFiles:
        (dirName, fileName) = os.path.split(filePath)
        (base, ext) = os.path.splitext(fileName)
        if base in catalog:
            existing.add(base)
        else:
            print(f'\tWARNING: downloaded photo for {base} not in catalog')
    print(f'{len(existing):>4} tablets already downloaded')
    downloadees = catalog - existing

    print(f'Going to fetch {len(downloadees)} photos from CDLI')

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    failed = set()
    for (i, pNum) in enumerate(sorted(downloadees)):
        url = f'{CDLI_URL}/{pNum}.jpg'
        sys.stderr.write(f'\t{i:>4} {pNum:<20} {len(failed):>4} failed\r')
        try:
            with urlopen(url, context=ctx) as uh:
                image = uh.read()
            with open(f'{PHOTO_FROM}/{pNum}.jpg', 'wb') as wh:
                wh.write(image)
        except Exception:
            failed.add(pNum)

    print(f'\t{len(downloadees) - len(failed):>4} {pNum:<20}')
    if failed:
        failedStr = '\n\t'.join(sorted(failed))
        print(f'\t{failedStr}')
    print(f'WARNING: {len(failed)} photos could not be downloaded')


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
    sys.stderr.write(f'{len(items)} images to convert\n')

    for (i, (base, fromFile, toFile)) in enumerate(sorted(items)):
        sys.stderr.write(f'{i+1:>5} {base:<30}\r')
        run([shellCommand] + optionsIn + [fromFile] + optionsOut + [toFile])
    sys.stderr.write('\n')


if len(sys.argv) <= 1:
    print(help)
command = sys.argv[1]

if command == 'scrape':
    doScrape()
elif command == 'photos':
    doImages(
        PHOTO_FROM, PHOTO_TO, PHOTO_COMMAND, PHOTO_OPTIONS_IN,
        PHOTO_OPTIONS_OUT, command, *PHOTO_EXT
    )
elif command == 'tablets':
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
