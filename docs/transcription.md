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

Node types
==========

We discuss the node types we are going to construct. A node type corresponds to
a textual object. Some node types will be marked as a section level.

All nodes that correspond directly to a line in the corpus,
also get features by which you can retrieve the original transcription:

* *srcLn* the literal contents of the line in the source
* *srcLnNum* the line number of the corresponding line in the source

Tablet
------

Nodes of type *tablet* correspond to the transcription of a tablet.

**This node type is section level 1.**

Our corpora are just sets of tablets. The position of a particular tablet in the
whole set is not meaningful. The main identification of tablets is by their
catalog identifier (in this case *P number*), not by any sequence number within
the corpus.

In the transcriptions we the start of a tablet marked as `@tablet`, although it
is sometimes missing.

The surest sign of the beginning of a tablet is a line like

    &P002174 = ATU 6, pl. 48, W 14731,?4

Here we collect `P002174` as the *catalogId* of the tablet, and
`ATU 6, pl. 48, W 14731,?4` as the tablet *name*.

We also add the name of the corpus as a feature *period* to the node type
*tablet*.

Subsequent lines starting with `#` are treated as comment lines. See below.

Subsequent lines of the form

    @object text

are used to fill the feature *object*. It will have as value whatever `text` is.

Face
----

The material of a tablet is divided into *faces* and then into *columns*.

A node of type *face* corresponds to the material after a face specifier and
before the next face specifier or the end of a tablet.

This node type is not a section level.

A face specifier looks like this:

    @obverse

or

    @reverse

There are a few other possibilities:

    @bottom
    @left
    @top
    @surface identifier
    @seal identifier

We make a feature *type* for this node type, which contains the name of the
face.

We also make a feature *identifier*, which contains the identifier if the kind
is `surface` or `seal`.

`@seal` is never followed by linguistic content. We will consider this to be a
face, and we will insert a special, empty sign in it, so that a seal can be
positioned in the stream of the text.

### fragment ###

There is another subdivision, very occasionally:

    @fragment identifier

This is really between tablet and face. But it occurs only in one tablet, which
is too rare to merit a separate node type.

We make a feature *fragment* for node type *face*, which will be filled by the
identifier of a preceding `@fragment`.

Column
------

The material of a *face* is divided into *columns* and then into *lines*.

A node of type *column* corresponds to the material after a column specifier and
before the next next column specifier or the end of a face or tablet.

**This node type is section level 2.**

Columns are marked by lines like

    @column number

There might be a prime `'` after the number, but before the last `.` If present,
it indicates that the number does not count objects on the tablet in its
original state, but in its present state. If the tablet is damaged, material is
missing, and the missing items are not numbered.

In the presence of a prime, we add to the *column* a feature *countPresent* with
value `1`.

Line
----

The material of a *column* is divided into *lines* and then into *quads*.

A node of type *line* corresponds to the material of a single line that starts
with a number.

**This node type is section level 3.**

If we encounter a line without a preceding column specifier, we proceed as if we
have seen a `@column 1`.

This is an example line.

    1.b1. , (EN~a DU ZATU759)a

Note that the number is a hierarchical number, with alternating digits and
letters. We strip the `.`s. The number is used to group the lines into *cases*
and *subcases*, see below.

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

Lines starting with `$` or `#` are comments to the current object (tablet, face,
column, or line).

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

Case and subcase
----------------

Lines can be grouped in chunks, which we call *cases* and *subcases*.

All lines in a face that start with the same number, form a *case*. The number
itself is recorded in the feature *number* on the node type *case*.

So lines with numbers `1a`, `1b`, and `2` form two cases: one with number `1`,
containing lines `1a` and `1b`, and one with number `2`, containing just line
`2`.

If the numbers show deeper hierarchy, we build *subcases*. Lines with numbers
`1a1`, `1a2`, `1b`, and `2` form (again) two cases. The case with number `1` has
two *subcases*: one with number `1a`, containing lines `1a1` and `1a2`, and one
with number `1b`, containing just line `1b`.

Cases and subcases represent squares on a tablet. The deepest levels are
degenerated squares, they have just one dimension: they are lines.

Quad and subquad
----------------

Lines are subdivided in *quads*. A quad is an atomic piece of space on a tablet
in a geometrical sense.

However, a quad can be filled by more than one *sign*. So, from a textual
perspective, a *quad* is not yet the basic level.

We get quads from lines by splitting the line material (the part after the
number) on white space.

There is one complication: the comma between numerals and other signs. They do
not correspond to signs on the tablet, but have been added in order to
facilitate searching.

We remove all commas in lines.

    1.a. 3(N01) , APIN~a 3(N57) UR4~a
    1. 2(N01) , 3(N57)
    1. [...] , 1(N39~a)#

After the splitting, we end up with top-level quads.

Quads may have internal structure.

A quad may be delimited by `| |` :

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

*   a single *sign*, which is either

    *   a numeral like `1(N57)`, or
    *   a string of letters, numbers

*   a composite of *subquads*, which is either
    *   a string having a `,` in it: the immediate subquads are obtained by
        splitting on the `,`; or
    *   a string delimited by `| |`; the immediate subquads are obtained by
        splitting on one of the operators.

Every subquad is one of:

*   a single *sign* (as in quad)
*   a composite of subquads, which is
    *   a string delimited by `( )`; the immediate subquads are obtained by
        splitting on one of the operators.

Operators are single characters, one of `x % @ & . : +`.

There is no space between the operators and the subquads.

Signs, subquads and quads may contain primes (`'`), variant markings
(`~`letter), or flags (`#?` or `!(`material`)`) or modifiers (`@`letter).

See for each type of object what augments may occur.

### Edges for (sub)quads ###

We represent the structure of quads and subquads by means of relationships:

*   *parent* : from sign or subquad to immediate parent; quads do not have a
    parent;
*   *child* : from (sub)quad to immediate children; signs do not have children;
*   *left*: from sign or subquad to left sibling;
*   *right*: from sign or subquad to right sibling.

For *left* and *right* we have:

*   edges are labeled with the operator that connects the two operands;
*   quads do not have left and right edges.

There is a bit of redundancy here. We apply it, because it will make search
operations easier in the resulting dataset.

### Variants ###

Quads, subquads and signs may have variants. This is indicated by a `~` and then
a letter.

This indicates that the tablet has a variant of the grapheme denoted by quad,
subquad or sign in question. For practical purposes it might be a completely
different grapheme.

    1.c. , (PIRIG~b1)a
    3.  1(N01) 1(N39~a) 1(N24) 1(N28) ,

Note that a variant of a numeral is written within the brackets.

We collect the variant in the feature *variant=letter*.

### Flags ###

Quads and signs may have *flags*. Subquads do not have them. In transcription
they show up as a special trailing character. Flags code for damage or
confidence of sign name or correction.

#### Collation ####

Flag `*`.

Collected as *collation=1*

#### Damage ####

Flag `#`.

Collected as *damage=1*.

Example:

    1.  1(N48) 7(N34) 3(N14) , BARA2~a#

#### Uncertain ####

Flag `?` Unsure identification.

Collected as *uncertain=1*.

Example:

    1.  1(N45) 8(N14)# , X SZE~a MA2?

#### Correction ####

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

Cluster
-------

One or more quads may be bracketed by `( )` or by `[ ]` or by `< >`: together
they form a *cluster*.

    2.c. , (|GIR3~cxSZE3|# NUN~a# [...])a

    3.  [...] , [MU |ZATU714xHI@g~a|]

    4.b1. <7(N14) , GAN2>

Note that a cluster may contain just one quad.

### Proper names ###

Clusters with `( )` indicate proper names. The closing bracket is always
followed by the letter `a`.

Collected in a feature *properName=1*.

### Missing signs ###

Clusters with `[ ]` indicate that there are missing signs here.

Collected in a feature *missing=1*.

`[...]` denotes one or more missing signs. We do create a sign node for it, we
put its *grapheme* feature to `...`, and we add the feature *missing=1*.

Sign
----

This is the basic unit of writing. Several signs may fill the space of a *quad*,
the basic geometrical unit.

**The node type *sign* is our slot type in Text-Fabric.**

There are two kind of signs: numerals and ordinary.

### Numerals ###

An example of a numeral is:

    2(N19)

The string of letters and numbers denotes its *grapheme*.

Numerals may be augmented with *primes* and *variants* within the brackets, and
with *flags* and *modifiers* outside the brackets.

### Ordinary signs ###

An example of an ordinary sign is

    GAN2

Ordinary signs may be augmented with *variants*, *flags*, and *modifiers*.

### Signs in general ###

The defining trait of a sign is its *grapheme*.

We will collect the text of a sign, without variants and flags, and store it in
the sign feature *grapheme*.
If the sign is a numeral, this is the piece between the brackets (without augments)
We store he number before the brackets in numeral in feature *numValue*.

### Primes ###

If there is a prime at the end of a numeral grapheme, we collect it in feature *prime=1*.

### Variants ###

See above.

### Flags ###

We have encountered them for quads already, see above.

Note that flags on numerals come *after* the brackets.

    5.  , |NI~a.RU| GIBIL SU~a 3(N57)# GU7# [...]

### Modifier ###

The grapheme part of a sign may be followed by a `@` and then a letter. This comes
after the *variant*, see above.

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

### Missing signs ###

There are notations for missing signs.

    [...]

Warning
=======

In order to produce transcribed text you cannot rely on features of slots alone.
Unless we make an artificial suffix feature, containing all transcription text
between a sign and the next one. Alternatively, we could reproduce transcription
text by walking down the quad and subquad nodes.
