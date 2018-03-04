Cunei API
=========

About
-----

The module
[cunei.py](https://github.com/Dans-labs/Nino-cunei/blob/master/programs/cunei.py)
contains a number of handy functions to deal with TF nodes for cuneiform tablets
and
[ATF](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html)
transcriptions of them and [CDLI](https://cdli.ucla.edu) lineart.

Set up
------

In this repository, *cunei.py* resides in the *programs* directory. In order to
import it into a Jupyter notebook in a completely different directory, we have
to point Python's module path to it:

```python
import os
REPO = '~/github/Dans-labs/Nino-cunei'
PROGRAM_DIR = os.path.expanduser(f'{REPO}/programs')
sys.path.append(PROGRAM_DIR)
from cunei import Cunei
```

In order to use it, you have to instantiate the `Cunei` object by passing it the
api of Text-Fabric:

```python
SOURCE = 'uruk'
VERSION = '0.1'
CORPUS = f'{REPO}/tf/{SOURCE}/{VERSION}'
IMAGE_DIR = f'{REPO}/source/cdli/images'
TF = Fabric(locations=[CORPUS], modules=[''], silent=False )
api = TF.load('')
CUNEI = Cunei(api, IMAGE_DIR)
```

When `Cunei` is initializing, it scans the `IMAGE_DIR` and reports how many
lineart images it sees.

Usage
-----

Now you can call the methods of *cunei*, as follows. One of the methods is
`getOuterQuads(node)`. To call it, say

```python
outerQuads = Cunei.getOuterQuads(line)
```

API
---

### atfFromSign ###

Reproduces the ATF representation of a sign.

**Takes**

*   `n` a node; must have node type `sign`;
*   `flags=False` whether flags will be included;

**Returns**

*   a string with the ATF representation of the sign.

### atfFromQuad ###

Reproduces the ATF representation of a quad.

**Takes**

*   `n` a node; must have node type `quad`;
*   `flags=False` whether flags will be included;
*   `outer=True` whether the quad is to be treated as an outer quad;

**Returns**

*   a string with the ATF representation of the quad.

### atfFromOuterQuad ###

Reproduces the ATF representation of an outer quad *or* sign.

If you take an ATF transcription line with linguistic material on it, and you
split it on white space, and you forget the brackets that cluster quads and
signs, then you get a seuqence of outer quads and signs.

If you need to get the ATF representation for these items, this function does
conveniently produce them. You do not have to worry yourself about the sign/quad
distinction here.

**Takes**

*   `n` a node; must have node type `quad` or `sign`;
*   `flags=False` whether flags will be included;

**Returns**

*   a string with the ATF representation of the outer quad.

### atfFromCluster ###

Reproduces the ATF representation of a cluster. Clusters are bracketings of
quads that indicate proper names, uncertainty, or supplied material. In ATF they
look like `( )a` or `[ ]` or `< >`

**Takes**

*   `n` a node; must have node type `cluster`;
*   `seen=None` set of signs that already have been done;

**Returns**

*   a string with the ATF representation of the cluster. Sub-clusters will also be
    represented. Signs belonging to multiple nested clusters will only be
    represented once.

### getOuterQuads ###

Collects the outer quads and isolated signs under a node. Outer quads and
isolated signs is what you get if you split line material by white space and
remove cluster brackets.

**Takes**

*   `n` a node; typically a tablet, face, column, line, or case. This is the
    container of the outer quads;

**Returns**

*   a list of nodes, each of which is either a sign or a quad, and, in both cases,
    not contained in a bigger quad. The order of the list is the natural order on
    nodes: first things first, and if two things start at the same time: bigger
    things first.

**Implementation details**

A quad or sign is outer, if it is not the "sub" of an other quad. We can see
that by inspecting the **sub** edges that land into a quad or sign:
`E.sub.t(node)`.

However, there might be *clusters* around the node, and such a cluster will have
an outgoing **sub** edge to the node. Hence we should test whether all incoming
**sub** edges are not originating from an other quad.

### nodeFromCase ###

Very much like the built-in
[T.nodeFromSection](https://github.com/Dans-labs/text-fabric/wiki/Api#sectioning)
of Text-Fabric. It gives you a node, if you specify a terminal case, i.e. a
transcription line.

**Takes**

*   a 3-tuple `(` *tabletNumber*, *face*:*columnNumber*, *hierarchical line
    number* `)`; the hierarchical number may contain the original `.` that they
    often have in the transcriptions, but you may also leave them out;

**Returns**

*   the corresponding node, which will be of a terminal *case*, having as
    **fullNumber** the value you supplied as *hierarchical line number*. If no
    such node exists, you get `None` back.

### caseFromNode ###

Very much like the built-in
[T.sectionFromNode](https://github.com/Dans-labs/text-fabric/wiki/Api#sectioning)
of Text-Fabric. It gives you a section tuple, if you give it the node a terminal
case, i.e. a transcription line.

**Takes**

*   the node of a terminal case (these are the cases that have a full hierarchical
    number; these cases correspond to the individual numbered lines in the
    transcription sources;

**Returns**

*   a 3-tuple `(` *tabletNumber*, *face*:*columnNumber*, *hierarchical line
    number* `)`; the hierarchical number will not contain `.`s.

### lineart ###

Fetches lineart for a node, and return it in a way that it can be embedded in an
output cell.

**Takes**

*   one or more nodes; as far as they are of type `tablet`, `quad` or `sign`,
    lineart will be looked up for them;
*   an optional key (a string), specifying which of the available linearts for
    this node you want to use; if you want to know which keys are available
    for a node, call `lineart` with `key='xxx'`, or any non-existing key;
*   an optional list of key=value, such as `width=100`, `height=200`.

The result will be returned as a *row* of images.
Subsequent calls to `lineart()` will result in vertically stacked rows.
So you can control the two-dimensional layout of your images.

**Implementation details**

The images will be called in by a little piece of generated HTML, using
the `<img/>` tag.
This only works if the image is within reach.
To the images will be copied to a sister directory of the notebook.
The name of this directory is `cdli-imagery`.
It will be created on-the-fly when needed.
Copying will only be done if needed.
