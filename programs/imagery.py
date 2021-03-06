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

    tablets: transforms tablet lineart eps to jpg
    ideographs: crops ideograph lineart from jpg to jpg
    ideonames: rename ideograph files to make them compatible with windows
    photos: decreases the size of the jpegs of the tablets
    scrape: scrape tablet photos from cdli

ideonames should be run after all image operations have succeeded.
It will rename filenames by replacing the | | at the beginning and the end
by [ ]
'''

SOURCE = 'uruk'
VERSION = '1.0'
REPO_DIR = os.path.expanduser(f'~/github/Nino-cunei/{SOURCE}')
CATALOG = f'{REPO_DIR}/tf/{SOURCE}/{VERSION}/catalogID.tf'
PHOTO_QUALITY = '30%'
LINEART_DENSITY = '300x300'
LINEART_QUALITY = '50%'

CDLI_URL = 'https://cdli.ucla.edu/dl/photo'

# photos of tablets
# reduction in filesize by lowering jpg quality
#
PHOTO_FROM = f'{REPO_DIR}/_downloads/cdli_photos'
PHOTO_TO = f'{REPO_DIR}/sources/cdli/images/{VERSION}/tablets/photos'
PHOTO_COMMAND = '/usr/local/bin/magick'
PHOTO_OPTIONS_IN = []
PHOTO_OPTIONS_OUT = ['-quality', PHOTO_QUALITY]
PHOTO_EXT = ('jpg', 'jpg')

# linearts of tablets
# eps to pdf: remains a compact vector image of inifinite resolution
# but difficult in browsers
#
# TABLET_FROM = f'{REPO_DIR}/_downloads/cdli_epstextcopies'
# TABLET_TO = f'{REPO_DIR}/sources/cdli/images/tablets/lineart'
# TABLET_COMMAND = '/usr/local/bin/ps2pdf'
# TABLET_OPTIONS_IN = ['-dEPSCrop']
# TABLET_OPTIONS_OUT = []
# TABLET_EXT = ('eps', 'pdf')

# linearts of tablets
# eps to jpg (because of browsers)
# normal resolution, reasonable jpg quality
#
TABLET_FROM = f'{REPO_DIR}/_downloads/cdli_epstextcopies'
TABLET_TO = f'{REPO_DIR}/sources/cdli/images/{VERSION}/tablets/lineart'
TABLET_COMMAND = '/usr/local/bin/magick'
TABLET_OPTIONS_IN = ['-density', LINEART_DENSITY]
TABLET_OPTIONS_OUT = ['-quality', LINEART_QUALITY]
TABLET_EXT = ('eps', 'jpg')

# linearts of ideographs and numerals
# cropping: some images are small drawings on page-size canvases
# all ideographs will be cropped
#
IDEO_FROM = f'{REPO_DIR}/_downloads/archsignfiles_jpg'
IDEO_TO = f'{REPO_DIR}/sources/cdli/images/{VERSION}/ideographs/lineart'
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


def doNames(
    targetDir, targetExt
):
  renamed = 0
  kept = 0
  remaining = 0
  for (dirPath, dirNames, fileNames) in os.walk(targetDir):
    for fileName in fileNames:
      (base, ext) = os.path.splitext(fileName)
      ext = ext.lstrip('.')
      if ext != targetExt:
          continue
      newBase = base
      if base.startswith('|'):
        newBase = '[' + newBase[1:]
      if base.endswith('|'):
        newBase = newBase[0:-1] + ']'
      if newBase != base:
        renamed += 1
        os.rename(f'{dirPath}/{fileName}', f'{dirPath}/{newBase}.{targetExt}')
      else:
        kept += 1
      if '|' in newBase:
        remaining += 1
        print(f'| in file name: {dirPath}/{fileName}')
  print(f'{renamed:>4} renamed')
  print(f'{kept:>4} unchanged')
  print(f'{remaining:>4} with remaining | in the name')


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
elif command == 'ideonames':
    doNames(
        IDEO_TO,
        IDEO_EXT[1]
    )
else:
    print(help)
