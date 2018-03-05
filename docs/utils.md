Utils API
=========

About
-----

The module
[utils.py](https://github.com/Dans-labs/Nino-cunei/blob/master/programs/utils.py)
contains a number of low-level functions to deal with TF nodes for cuneiform
tablets. The focus is on comparing the data in TF with the original source data.

Set up
------

In this repository, *utils.py* resides in the *programs* directory. In order to
import it into a Jupyter notebook in a completely different directory, we have
to point Python's module path to it:

```python
import os
REPO = '~/github/Dans-labs/Nino-cunei'
SOURCE_DIR = os.path.expanduser(f'{REPO}/sources/cdli')
PROGRAM_DIR = os.path.expanduser(f'{REPO}/programs')
TEMP_DIR = os.path.expanduser(f'{REPO}/_temp')
sys.path.append(PROGRAM_DIR)
from utils import Compare
```

In order to use it, you have to instantiate the `Compare` object by passing it
the api of Text-Fabric:

```python
SOURCE = 'uruk'
VERSION = '0.1'
CORPUS = f'{REPO}/tf/{SOURCE}/{VERSION}'
TF = Fabric(locations=[CORPUS], modules=[''], silent=False )
api = TF.load('')
COMP = Compare(api, SOURCE_DIR, TEMP_DIR)
```

Usage
-----

Now you can call the methods of *utils*, as follows. One of the methods is
`getSource(node)`. To call it, say

```python
sourceLines = COMP.getSource(tablet)
```

API
---

### readCorpora ###

Read the ATF files from the `SOURCE_DIR`.

**Yields**

*   Transcription lines from the source files, in a succesion of tuples
    `(periodName, tabletName, lineNumber, lineString, isSkipping)`.

The period name is taken from the file name. For this corpus it will be either
`uruk-iii` or `uruk-iv`.

When there are duplicate tablet names, only the source lines of the first one
will be harvested. Subsequent tablets with the same name will be passed through,
but with `isSkipping` set to `False`. In all other cases, `isSkipping` is
`True`.

The resulting `line`-s have their newlines already stripped.

### checkSanity ###

Given a function to *grep* material from the source lines of the corpus, and a
function to grab material from the TF version of the corpus, we will conduct a
comparison, and report differences. We show a table of the *GREP* material
alongside a table of the *TF* material, up to the first difference. Both tables
have several columns. They always have columns containing positioning
information (period, tabletName, sourceLineNumber), and they may have additional
custom columns, depending on what material has been grabbed.

A number of rows leading up to the first difference, and a number of rows after
the first difference will be shown. The difference itself will be clearly
indicated.

If the test passes, it is a very strong indication that all is well. Not only
the data grabbed by each of the functions is identical, it also occurs in the
same sequence, at the same locations.

**Takes**

*   `headers` a list of names for the custom columns of data;
*   `grepFunc` a function that *greps* the lines of the corpus and delivers the
    matched lines as a tuple of fields;
*   `tfFunc` a function that walks the nodes of the TF dataset and delivers
    information found at selected nodes as a tuple of fields;
*   `leeway=0` sometimes the exact line number for things is lost in TF. `tfFunc`
    may guess the line number, but it might be a bit off. By setting `leeway` to a
    positive value, differences in line numbers smaller than that value will not
    lead to a nagative comparison result;

**Returns**

*   `True` if the GREP results and the TF results are identical. `False`
    otherwise. A comparison report is printed in all cases.
