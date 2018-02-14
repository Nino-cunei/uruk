About
=====

We describe how we model a few corpora of tablet transcriptions into
[Text-Fabric](https://github.com/Dans-labs/text-fabric) format.

We mention the concepts behind the transcriptions and how they translate to the
Text-Fabric model.

The Text-Fabric model views the text as a series of atomic units, called
*slots*. On top of that, textual objects can be represented as *nodes*. Every
node is linked to a subset of slots. Nodes can be related by means of edges.
Nodes and edges can be annotated with supplemental information. Text-Fabric
support 3 section levels. You may point to three types of nodes and declare them
to be sections of level 1, 2 and 3.

SLots and node types
====================

We discuss the node types we are going to construct. A node type corresponds to
a textual object. Some node types will be marked as a section level.

All nodes that correspond directly to a line in the corpus, also get features by
which you can retrieve the original transcription:

*   *srcLn* the literal contents of the line in the source
*   *srcLnNum* the line number of the corresponding line in the source

Sign
----

This is the basic unit of writing.

**The node type *sign* is our slot type in Text-Fabric.**

### Signs in general ###

The defining trait of a sign is its *grapheme*.

We will collect the text of a sign, without variants and flags, and store it in
the sign feature *grapheme*.

Graphemes may be *augmented* with

*   a prime
*   variants
*   flags
*   modifiers

There are two kind of signs: numerals and ordinary.

### Numerals ###

Examples of a numerals:

    2(N19)
    3(N57)#
    1(N24')

We store he number before the brackets in numeral in feature *repeat*. Within
the brackets you find the *grapheme*, possibly augmented with *prime* and
*variants*.

After the closing bracket the numeral may be augmented with *flags* and
*modifiers*.

### Ordinary signs ###

An example of an ordinary sign is

    GAN2

### Missing signs ###

This notation denotes missing signs.

    [...]

In the syntax of transcriptions, this is a one-element cluster, bracketed with
`[ ]`, with a special sign in it `...`, meaning: one or more missing graphemes.

We treat the `...` sign as a single sign `…`, and we treat the cluster as any
other cluster, see below.

### Augments ###

We describe the various kinds of augments. Not only individual signs may be
augmented, also more complex node types such as *quads* and *subquads* (see
below) may be augmented.

#### Prime ####

If there is a prime `'` at the end of a numeral grapheme, we collect it in
feature *prime=1*.

#### Variants ####

*Quads*, *subquads* and *signs* may have variants. This is indicated by a `~`
and then a letter.

This indicates that the tablet has a variant of the grapheme in question. That
might be a completely different grapheme.

    1.c. , (PIRIG~b1)a
    3.  1(N01) 1(N39~a) 1(N24) 1(N28) ,

Note that a variant of a numeral is written within the brackets.

We collect the variant in the feature *variant=letter*.

If there are more, we collect the values in a comma separated list.

#### Flags ####

*Quads* and *signs* may have *flags*. *Subquads* do not have them. In
transcription they show up as a special trailing character. Flags code for
things like damage, uncertainty, and correction.

##### Collation #####

Flag `*`.

Collected as *collation=1*

Not encountered yet.

##### Damage #####

Flag `#`.

Collected as *damage=1*.

Example:

    1.  1(N48) 7(N34) 3(N14) , BARA2~a#

##### Uncertain #####

Flag `?` Unsure identification.

Collected as *uncertain=1*.

Example:

    1.  1(N45) 8(N14)# , X SZE~a MA2?

##### Correction #####

Flag `!` or `!(` *written* `)`

A bare `!` is collected as *remarkable=1*

The full form indicates that the sign has been corrected (like in Hebrew
*ketiv/qere*).

The sign between the brackets is what is written (ketiv), the sign before the
`!` is the corrected form (qere).

Collected as *remarkable=1*, *written=written*.

Example:

    5.  1(N01) , NAM2 URU~a1!(GURUSZ~a)?

Note that flags on a numeral are written within the brackets.

There may be multiple flags:

    1.  1(N48) 7(N34) 3(N14) , BARA2~a#

#### Modifiers ####

The grapheme part of a sign may be followed by a `@` and then a letter. This
comes after the *variant*, see above.

    2.a. 1(N01) , TUG2~a@g
    7.b. , SU~a# NAB# DI |E2~ax1(N57)@t|

Possible modifiers are:

code | meaning
---- | -------
c | curved
f | flat
g | gunu (4 extra wedges)
s | sheshig (added še-sign)
t | tenu (slanting)
n | nutillu (unfinished)
z | zidatenu (slanting right)
k | kabatenu (slanting left)
r | vertically reflected
h | horizontally reflected

Note that a modifier of a numeral is written within the brackets.

We collect the modifier in the sign feature *modifier=letter*.

If there are more, we collect the values in a comma separated list.

Quad and subquad
----------------

A *quad* is an atomic piece of space on a tablet in a geometrical sense. Quads
are filled with a single *sign* or a composition of signs. The composition may
be a nest of *subquads*.

We get quads from transcription lines by splitting the line material (the part
after the number) on white space.

There is one complication: the comma between numerals and other signs. They do
not correspond to signs on the tablet, but have been added in order to
facilitate searching.

We remove all commas in lines.

    1.a. 3(N01) , APIN~a 3(N57) UR4~a
    1. 2(N01) , 3(N57)
    1. [...] , 1(N39~a)#

Quads may have internal structure. Such quads are delimited by `| |` (there are
a few exceptions):

    5.  1(N01) , |DUG~bx1(N57)|

The quad `|DUG~bx1(N57)|` is the composition of two *subquads* : `DUG~b` and
`1(N57)`, composed by operator `x`.

There are several operators, and the composition may involve several levels. If
that is the cases, brackets specify the construction:

    2.  4(N01) 1(N39~a) 1(N24) , |NINDA2x(HI@g~a.1(N06))|

The quad `|NINDA2x(HI@g~a.1(N06))|` is the composition by `x` of subquads
`NINDA2` and `HI@g~a.1(N06)` and the latter is the composition by `.` of
subquads `HI@g~a` and `.1(N06)`.

We can now state the rules a bit more precisely.

If we take line material, remove `,` and then split on whitespace, we get the
objects that correspond to *quads*.

Every quad is one of:

*   a single *sign*, possibly augmented, or
*   a composite of *subquads*, delimited by `| |`

Every subquad is one of:

*   a single *sign*, possibly augmented (as in quad)
*   a composite of subquads, which is
    *   a string, possibly delimited by `( )`, possibly augmented; the immediate
        subquads are obtained by splitting on one of the operators.

Operators are single characters, one of `x % @ & . : +`.

There is no space between the operators and the subquads.

### Edges for (sub)quads ###

We represent the structure of quads and subquads by means of edges:

*   *op*: from sign or subquad to right sibling;

For *op* we have:

*   edges are labeled with the operator that connects the two operands;
*   quads do not have *op* edges (as opposed to *subquads*).

Note that in TF we can traverse edges in both directions.

Cluster
-------

One or more *quads* may be bracketed by `( )` or by `[ ]` or by `< >`: together
they form a *cluster*.

    2.c. , (|GIR3~cxSZE3|# NUN~a# [...])a

    3.  [...] , [MU |ZATU714xHI@g~a|]

    4.b1. <7(N14) , GAN2>

Note that a cluster may contain just one quad.

### Proper names ###

Clusters with `( )` indicate proper names. The closing bracket is always
followed by the letter `a`.

Collected in a feature *kind=properName*.

### Missing signs ###

Clusters with `[ ]` indicate that there are missing signs here.

Collected in a feature *kind=uncertain*.

### Supplied signs ###

Clusters with `< >` indicate that these signs have been supplied in order to
make sense.

Collected in the feature *kind=supplied*

Line
----

A sequence of *quads* forms a line.

A node of type *line* corresponds to the material of a single line that starts
with a number.

**This node type is section level 3.**

If we encounter a line without a preceding column specifier, we proceed as if we
have seen a `@column 1`.

This is an example line.

    1.b1. , (EN~a DU ZATU759)a

Note that the number is a hierarchical number, with alternating digits and
letters. We strip the `.`s. The number is used to group the lines into *cases*,
see below.

Like the numbers of columns, line numbers may have a `'` at the end. In the
presence of a prime, we add to the *line* a feature *countPresent* with value
`1`.

### Crossrefs ###

Lines can be cross referenced with lines on other tablets (not necessarily
within this corpus). A cross-reference consists of a line after the source line:

    1.  1(N01) , |1(N57).SZUBUR|
    >> P000014 oi2

    1'. [1(N01)] , [...]
    >>Q000023 026 ?

This means that line `1.` corresponds to line `oi2` in text `P000014` and that
line `1'.` corresponds to line `026` in text `Q000023`, although with
uncertainty.

We collect this information in the feature *crossref* on lines, with value
`P000014.oi2` and `Q000023.026:?` respectively.

If there are several cross-references from the same line, we collect them in a
comma separated list.

### Comments ###

Lines starting with `$` or `#` are comments to the current object (*tablet*,
*face*, *column*, or *line*, see below).

    &P002718 = ATU 3, pl. 078, W 17729,cn+
    #version: 0.1
    #atf: lang qpc

and

    4.  1(N01) , [...]
    $ rest broken
    @column 3
    $ beginning broken

We collect them in a feature *comments*. If there are several comment lines for
the same object, we combine them into one string, separated by a newline.

Case
----

Lines are grouped in *cases*, based on their number.

All lines in a *column* (see below) that start with the same number, form a
*case*. The number itself is recorded in the feature *number* on the node type
*case*.

So lines with numbers `1a`, `1b`, and `2` form two cases: one with number `1`,
containing lines `1a` and `1b`, and one with number `2`, containing just line
`2`.

If the numbers show deeper hierarchy, we build sub-cases. Lines with numbers
`1a1`, `1a2`, `1b`, and `2` form (again) two cases. The case with number `1` has
two *cases*: one with number `1a`, containing lines `1a1` and `1a2`, and one
with number `1b`, containing just line `1b`.

Cases represent squares on a tablet. The deepest levels are degenerated squares,
they have just one dimension: they are the *lines*.

Column
------

Cases are grouped into *columns*.

Columns are marked by lines like

    @column number

A node of type *column* corresponds to the material after the *column* specifier
and before the next next *column* specifier or the end of a *face* or *tablet*.

**This node type is section level 2.**

There might be a prime `'` after the number, but before the last `.` If present,
it indicates that the number does not count objects on the tablet in its
original state, but in its present state. If the tablet is damaged, material is
missing, and the missing items are not numbered.

In the presence of a prime, we add to the *column* a feature *countPresent* with
value `1`.

Face
----

Columns are grouped into *faces*.

Faces are marked by lines like

    @obverse

or

    @reverse

There are a few other possibilities:

    @bottom
    @left
    @top
    @surface identifier
    @seal identifier

A node of type *face* corresponds to the material after a *face* specifier and
before the next *face* specifier or the end of a *tablet*.

**This node type is not a section level!**

We make a feature *type* for this node type, which contains the name of the
face, e.g. `obverse`, `reverse`.

We also make a feature *identifier*, which contains the identifier if the kind
is `surface` or `seal`.

`@seal` is never followed by linguistic content.

### fragment ###

There is another subdivision, very occasionally:

    @fragment identifier

This is really between *tablet* and *face*. But it occurs only in one tablet,
which is too rare to merit a separate node type.

We make a feature *fragment* for node type *face*, which will be filled by the
identifier of a preceding `@fragment`.

Tablet
------

*Faces* are grouped into *tablets*.

*Tablets* are marked by lines like

    @tablet

Sometimes this line sometimes missing.
The surest sign of the beginning of a tablet is a line like

    &P002174 = ATU 6, pl. 48, W 14731,?4

Here we collect `P002174` as the *catalogId* of the tablet, and
`ATU 6, pl. 48, W 14731,?4` as the tablet *name*.

We also add the name of the corpus as a feature *period* to the node type
*tablet*.

A node of type *tablet* corresponds to the material after a *tablet* specifier and
before the next *tablet* specifier.

**This node type is section level 1.**

Our corpora are just sets of tablets. The position of a particular tablet in the
whole set is not meaningful. The main identification of tablets is by their
catalog identifier (in this case *P number*), not by any sequence number within
the corpus.

Subsequent lines starting with `#` are treated as comment lines. See above.

Subsequent lines of the form

    @object text

are used to fill the feature *object*. It will have as value whatever `text` is.

Empty objects
=============

If tablets, faces, columns or lines lack linguistic material,
they will not have slots.
This is incompatible with the Text-Fabric model, where all nodes must be anchored to the slots.
We will take care that if linguistic material is missing, we insert a special sign.
This is a sign with *grapheme=''*, the empty string. 

Warning
=======

In order to produce transcribed text you cannot rely on features of slots alone.
Unless we make an artificial suffix feature, containing all transcription text
between a sign and the next one. Alternatively, we could reproduce transcription
text by walking down the quad and subquad nodes.
