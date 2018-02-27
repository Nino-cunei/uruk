Feature documentation
=====================

Here you find a description of the transcriptions of the Uruk corpora, the
Text-Fabric model in general, and the node types, features and edges for the
Uruk corpora in particular.

Conversion from ATF to TF
-------------------------

Below is a description of tablet transcriptions in
[ATF](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html)
and an account how we transform them into
[Text-Fabric](https://github.com/Dans-labs/text-fabric/wiki) format by means of
[tfFromAtf.py](https://github.com/Dans-labs/Nino-cunei/blob/master/programs/tfFromAtf.py).

The Text-Fabric model views the text as a series of atomic units, called
*slots*. In this corpus [*signs*](#sign) are the slots.

On top of that, more complex textual objects can be represented as *nodes*. In
this corpus we have node types for: [*sign*](#sign), [*quad*](#quad),
[*cluster*](#cluster), [*case*](#case), [*line*](#line), [*comment*](#comment),
[*column*](#column), [*face*](#face), [*tablet*](#tablet),

The type of every node is given by the feature
[**otype**](https://github.com/Dans-labs/text-fabric/wiki/Api#warp-feature-otype).
Every node is linked to a subset of slots by
[**oslots**](https://github.com/Dans-labs/text-fabric/wiki/Api#warp-feature-oslots).

Nodes can be related by means of edges.

Nodes and edges can be annotated with features. See the table below.

Text-Fabric supports three customizable section levels. In this corpus they are
[*tablet*](#tablet), [*column*](#column), [*line*](#line).

Reference table of features
===========================

*(Keep this under your pillow)*

Node type [*sign*](#sign)
-------------------------

Basic unit containing a single `grapheme` and zero or more *augments*.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**collation** | `0` `1` | `*` | indicates the presence of the *collation* flag `*` (not in this corpus)
**damage** | `0` `1` | `IDIGNA#` | indicates the presence of the *damage* flag `#`
**grapheme** | `N14` `GISZ` | `N14` `GISZ` | the name of a [*sign*](#sign) (excluding repeats and augments)
**modifier** | `n` `g` `t` | `GUM@n~b` `KUR@g~a` | a modifier `@` of a grapheme in a sign
**modifierFirst** | `1` `0` | `URUDU@g~c` resp. `AB~a@g` | whether the modifier `@` comes before the variant `~` or not
**modifierInner** | `f` | `7(N34@f)` | a modifier `@` that occurs inside a *repeat*
**prime** | `1` `0` | `1(N24')` | whether a [*sign*](#sign) has a prime `'`
**remarkable** | `1` `0` | `ABGAL!` | indicates the presence of the *remarkable* flag `!`
**repeat** | `4` | `4(N01)` | marks repetition of a grapheme
**uncertain** | `1` `0` | `DU6~b?` | indicates the presence of the *uncertain* flag `?`
**variant** | `a` `b` | `APIN~a` `SIG2~a1` | a variant `~` aka allograph of a grapheme
**written** | `KASKAL` | `APIN!(KASKAL)` | indicates the presence of a flag with a correction `!(`*grapheme*`)`

edges | to | values | description
----- | --- | ------ | -----------
**op** | [*quad*](#quad) [*sign*](#sign) | `x` `+` `.` | links a quad or sign to its right sibling in a containing quad; the value of the edge contains the [operator](#operators) used in the composition

Node type [*quad*](#quad)
-------------------------

Composite of [*signs*](#sign). The composite itself may be augmented.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**collation** | `0` `1` | `*` | indicates the presence of the *collation* flag `*` (not in this corpus)
**damage** | `0` `1` | `\|(SZAxHI@g~a)~b\|#` | indicates the presence of the *damage* flag `#`
**modifier** | `n` `g` `t` | `E2~bx1(N57)@t` | a modifier `@` of a (sub)-[*quad*](#quad) as a whole
**remarkable** | `1` `0` | no examples | indicates the presence of the *remarkable* flag `!`
**uncertain** | `1` `0` | `\|NINDA2xAN\|?` | indicates the presence of the *uncertain* flag `?`
**variantOuter** | `a` | `(U8xTAR)~b` | a variant `~` of a(sub)-[*quad*](#quad)
**written** |  | no examples | indicates the presence of a flag with a correction `!(`*grapheme*`)`

edges | to | values | description
----- | --- | ------ | -----------
**op** | [*quad*](#quad) [*sign*](#sign) | `x` `+` `.` | links a quad or sign to its right sibling in a containing quad; the value of the edge contains the [operator](#operators) used in the composition
**sub** | [*quad*](#quad) [*cluster*](#cluster) [*case*](#case) | none | links the parent node in a nested structure to its child nodes

Node type [*cluster*](#cluster)
-------------------------------

Grouped sequence of [*quads*](#quad) and [*signs*](#sign). There are different
types of these bracketings. Clusters may be nested.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**type** | `uncertain` `properName` `supplied` | `[ ]` `( )a` `< >` | type of cluster

edges | to | values | description
----- | --- | ------ | -----------
**sub** | [*quad*](#quad) [*cluster*](#cluster) [*case*](#case) | none | links the parent node in a nested structure to its child nodes

Node type [*case*](#case)
-------------------------

Subdivision of a containing [*line*](#line) or [*case*](#case). The lowest level
cases contain sequences of [*quads*](#quad) and [*signs*](#sign). Cases are
numbered with a hierarchical number.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**crossref** | `Q000026.007` | `>>Q000026 007` crossreference to *tablet*.*line* in same or other corpus | 
**fullNumber** | `1` `1a` `1b1` | `1.` `1.a.` `1.b1.` | hierarchical number of a [*case*](#case); present on each transcription [*line*](#line) with text material
**number** | `a` `1` |  | relative number of a [*case*](#case) within its containing case or lin column; see also **fullNumber**
**origNumber** | `1` |  | original number of a [*case*](#case) if there were conversion issues; see also **badNumbering**
**prime** | `1.c'. N? , X` | whether a case number has a prime `'` | 
**srcLn** |  |  | the literal text in the transcription at the start of the object; see [source data](#source-data)
**srcLnNum** |  |  | the line number of the transcription line at the start of the object; see [source data](#source-data)

edges | to | values | description
----- | --- | ------ | -----------
**sub** | [*quad*](#quad) [*cluster*](#cluster) [*case*](#case) | none | links the parent node in a nested structure to its child nodes

Node type [*line*](#line)
-------------------------

Subdivision of a containing [*column*](#column) or [*face*](#face). Lines maybe
divided in [*cases*](#case); if there is no subdivision. There is a single
[*case*](#case) as big as the line.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**number** | `1` |  | relative number of a [*line*](#line) within its containing column; see also **fullNumber**.

Node type [*comment*](#comment)
-------------------------------

There are several types of comment nodes:

*   metadata (`#`)
*   object information (`@object`)
*   ruling (`$`)

Comments are targeted to [*tablets*](#tablet), [*faces*](#face),
[*columns*](#column), [*lines*](#line) or [*cases*](#case).

feature | values | in ATF | description
------- | ------ | ------ | -----------
**srcLn** |  |  | the literal text in the transcription at the start of the object; see [source data](#source-data)
**srcLnNum** |  |  | the line number of the transcription line at the start of the object; see [source data](#source-data)
**text** | `atf: lang qpc` | `#atf: lang qpc` | text of a m`meta`data comment
**text** | `composite text` | `@object composite text` | text of an `object` comment
**text** | `beginning broken` | `$ beginning broken` | text of `ruling`
**type** | `meta` `object` `ruling` | `#` `$` `@object` | type of comment line; see also **text**

edges | from | values | description
----- | ---- | ------ | -----------
**comments** | various | none | links a node to each of its [*comments*](#comment).

Node type [*column*](#column)
-----------------------------

Primary division of a [*face*](#face). Columns are divided into
[*lines*](#line); [*columns*](#column) are numbered.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**badNumbering** | `1` `2` |  | whether there are issues with the numbering of [*lines*](#line) and [*cases*](#case) in the [*column*](#column); case numbers in TF may be different from the originals in transcription: see also **origNumber**
**fullNumber** | `obverse:2` `reverse:1` | **number** of a *column* preceded by the **type** of its [*face*](#face) | 
**number** | `1` `2` | `@column 1` `@column 2'` | column number; without prime, see also **prime**
**prime** | `1` `0` | `@column 1'` | whether a column number has a prime `'`
**srcLn** |  |  | the literal text in the transcription at the start of the object; see [source data](#source-data)
**srcLnNum** |  |  | the line number of the transcription line at the start of the object; see [source data](#source-data)

Node type [*face*](#face)
-------------------------

One of the sides of a [*tablet*](#tablet).

feature | values | in ATF | description
------- | ------ | ------ | -----------
**fragment** | `a` `b` | `@fragment a` | fragment of the [*tablet*](#tablet) the [*face*](#face) is on (very rare in the Uruk corpus)
**identifier** | `a` `X` | `@surface a` `@surface X` | addition of to the [*face*](#face) identifier
**srcLn** |  |  | the literal text in the transcription at the start of the object; see [source data](#source-data)
**srcLnNum** |  |  | the line number of the transcription line at the start of the object; see [source data](#source-data)
**type** | `obverse` `reverse` | `@obverse` `@reverse` | type of face, additional specs after the keyword go into **identifier**

Node type [*tablet*](#tablet)
-----------------------------

The main entity of which the corpus is composed, representing the transcription
of a complete clay tablet.

feature | values | in ATF | description
------- | ------ | ------ | -----------
**catalogId** | `P005381` | `&P005381` | the identification of a [*tablet*](#tablet)
**name** | `MSVO 3, 70` | `&P005381 = MSVO 3, 70` | the part after the `=` in the identification line of a tablet
**period** | `uruk-iii` `uruk-iv` |  | the period the tablet belongs to, derived from the source file name
**srcLn** |  |  | the literal text in the transcription at the start of the object; see [source data](#source-data)
**srcLnNum** |  |  | the line number of the transcription line at the start of the object; see [source data](#source-data)

Source data
===========

All nodes that correspond directly to a line in the corpus, also get features by
which you can retrieve the original transcription:

*   **srcLn** the literal contents of the line in the source;
*   **srcLnNum** the line number of the corresponding line in the source.

Slots
=====

We discuss the node types we are going to construct. A node type corresponds to
a textual object. Some node types will be marked as a section level.

Sign
----

This is the basic unit of writing.

**The node type [*sign*](#sign) is our slot type in Text-Fabric.**

### Signs in general ###

The defining trait of a sign is its *grapheme* or *glyph*.

We will collect the name string of a sign, without variants and flags, and store
it in the sign feature **grapheme**.

Graphemes may be *augmented* with

*   a prime
*   variants
*   flags
*   modifiers

Graphemes may be repeated. Numerals are repeated quite often.

### Repeats ###

Examples of a repeats (the first three are numerals):

    2(N19)
    3(N57)#
    1(N24')
    4(LAGAB~a)
    N(N01)|#

We store the number before the brackets in a feature called **repeat**. If the
number is `N`, it means that a number is missing. In this case we set the
**repeat** to `-1`.

Within the brackets you find the *grapheme*, possibly augmented with *prime* and
*variant* and *modifier*.

Modifiers may also occur after the closing bracket of a repeat.

After the closing bracket the repeated grapheme may be augmented with *flags*.

A modifier is generally stored in the feature **modifier**. But a modifier
within the brackets of a repeat is stored in the feature **modifierInner**. In
this way you can distinguish between the two cases later on.

### Ordinary signs ###

An example of an ordinary sign is

    GAN2

### Missing signs ###

This notation denotes missing signs.

    [...]

In the syntax of transcriptions, this is a one-element [*cluster*](#cluster),
bracketed with `[ ]`, with a special sign in it `...`, meaning: one or more
missing graphemes.

We treat the `...` sign as a single sign `…`, and we treat the cluster as any
other cluster.

### Augments ###

We describe the various kinds of augments. Not only individual signs may be
augmented, also more complex node types such as [*quads*](#quad) may be
augmented.

#### Prime ####

If there is a prime `'` at the end of a numeral grapheme, we collect it in
feature **prime** = `1`.

#### Variants ####

[*Quads*](#quad) and *signs* may have variants, also called *allographs*. This
is indicated by a `~` and then a sequence of letter and digits except the letter
`x`. `x` is an *operator*, see below.

This indicates that the tablet has a variant of the grapheme in question. That
might be a completely different grapheme.

    1.c. , (PIRIG~b1)a
    3.  1(N01) 1(N39~a) 1(N24) 1(N28) ,

Note that a variant of a numeral is written within the brackets.

We collect the variant in the feature **variant** = *letter* or **variantOuter**
= *letter*. If the variant is directly on a sign, we use **variant**, if it is
on a complex quad, we use **variantOuter**.

If there are more variants, we collect the values in a comma separated list.

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

We collect the modifier in the sign feature **modifier** = *letter*.

If there are more modifiers, we collect the values in a comma separated list.

##### Order of variants and modifiers #####

Variants and modifiers may occur both, and in both orders.

Examples (both in the same tablet P257531:

    2.b. 2(N05) 2(N42~a) , HI@g~a
    1.a. 2(N01) , U4 SZEN~c@t

We consider the order *variant-modifier* as the default. If we encounter the
order *modifier-variant* we mark it as **modifierFirst** = `1`.

#### Flags ####

Outer [*quads*](#quad) and *signs* may have *flags*. Sub-*quads* do not have
them. In transcription they show up as a special trailing character. Flags code
for things like damage, uncertainty, and correction.

##### Collation #####

Flag `*`.

Collected as **collation** = `1`

Not encountered yet.

##### Damage #####

Flag `#`.

Collected as **damage** = `1`

Example:

    1.  1(N48) 7(N34) 3(N14) , BARA2~a#

##### Uncertain #####

Flag `?` Unsure identification.

Collected as **uncertain** = `1`.

Example:

    1.  1(N45) 8(N14)# , X SZE~a MA2?

##### Correction #####

Flag `!` or `!(` *written* `)`

A bare `!` is collected as **remarkable** = `1`

The full form indicates that the sign has been corrected (like in Hebrew
*ketiv/qere*).

The sign between the brackets is what is written (ketiv), the sign before the
`!` is the corrected form (qere).

Collected as **written** = *written*. In this case, we do not set the
**remarkable** feature to `1`.

Example:

    5.  1(N01) , NAM2 URU~a1!(GURUSZ~a)?

Note that flags on a numeral are written within the brackets.

There may be multiple flags:

    1.  1(N48) 7(N34) 3(N14) , BARA2~a#

The other nodes
===============

Quad
----

A *quad* is an atomic piece of space on a tablet in a geometrical sense. *Quads*
are filled with a single [*sign*](#sign) or a composition of signs. The
composition may be a nest of *quads* and [*signs*](#sign).

We get *quads* from transcription lines by splitting the line material (the part
after the number) on white space.

There is one complication: the comma between numerals and other
[*signs*](#sign). They do not correspond to signs on the tablet, but have been
added in order to facilitate searching.

We remove all commas in lines.

    1.a. 3(N01) , APIN~a 3(N57) UR4~a
    1. 2(N01) , 3(N57)
    1. [...] , 1(N39~a)#

*Quads* may have internal structure. Such quads are delimited by `| |` (there
are a few exceptions):

    5.  1(N01) , |DUG~bx1(N57)|

The quad `|DUG~bx1(N57)|` is the composition of two sub-*quads* : `DUG~b` and
`1(N57)`, composed by operator `x`.

There are several operators, and the composition may involve several levels. If
that is the case, brackets specify the construction:

    2.  4(N01) 1(N39~a) 1(N24) , |NINDA2x(HI@g~a.1(N06))|

The *quad* `|NINDA2x(HI@g~a.1(N06))|` is the composition by `x` of sub-*quads*
`NINDA2` and `HI@g~a.1(N06)` and the latter is the composition by `.` of
sub-*quads* `HI@g~a` and `.1(N06)`.

We can now state the rules a bit more precisely.

If we take line material, remove `,` and then split on whitespace, we get the
objects that correspond to *quads*.

Every *quad* is one of:

*   a single [*sign*](#sign), possibly augmented, or
*   a composite of outermost *quads*, delimited by `| |`

Every non-outermost quad is one of:

*   a single [*sign*](#sign), possibly augmented (as in *quad*)
*   a composite of sub-*quads*, which is
    *   a string, possibly delimited by `( )`, possibly augmented; the immediate
        sub-*quads* are obtained by splitting on one of the operators.

### Augments ###

Like [*signs*](#sign), quads may have *augments*. Quads do not take primes.

Variants on quads as a whole are collected in **variantOuter** instead of in
**variant**.

### Operators ###

Operators are single characters, one of `x % & . : +`.

According to ORACC, `@` is also an operator. However, `@` is also a modifier,
and `@` also seems to be a part of a grapheme. So, splitting on `@` to get
sub-*quads*, is a bad idea. Looking into the corpus, we do not see cases where
`@` is not a modifier, except:

    1'. , U4 |U4x1(N01)| SUKUD@inversum? NA
    14'. 1(N01) , ASZ2#? KI@
    # traces of erased UKKIN~a, PA~a, KALAM?, MUD3~d, GI@i
    2. , U2@~b SAG KISZ

In all these cases, `@` does not seem an operator. So we remove `@` from the
list of operators.

There is no space between the operators and the sub-[*quads*](#quad).

### Edges for (sub-)*quads* ###

We represent the structure of *quads* and sub-*quads* by means of edges:

*   **sub**: from *quad* to any *quad* or [*sign*](#sign) embedded in it;
*   **op**: from [*sign*](#sign) or sub-*quad* to right sibling;

For **op** we have:

*   edges are labeled with the operator that connects the two operands;
*   outermost *quads* do not have **op** edges (as opposed to sub-*quads*).

Note that in TF we can traverse edges in both directions.

*   `E.sub.f(n)` gives you the children of node `n`;
*   `E.sub.t(n)` gives you the parent(s) of node `n`.

**N.B.:** *Quads* may have multiple parents: [*cluster*](#cluster) parents and
*quad* parents. Since there are several types of clusters, a quad may have
several cluster parents.

Cluster
-------

One or more [*quads*](#quad) may be bracketed by `( )` or by `[ ]` or by `< >`:
together they form a *cluster*.

    2.c. , (|GIR3~cxSZE3|# NUN~a# [...])a

    3.  [...] , [MU |ZATU714xHI@g~a|]

    4.b1. <7(N14) , GAN2>

Note that a cluster may contain just one [*quad*](#quad).

### Proper names ###

Clusters with `( )` indicate proper names. The closing bracket is always
followed by the letter `a`.

Collected in a feature **type** = `properName`

### Missing signs ###

Clusters with `[ ]` indicate that there are missing signs here.

Collected in a feature **type** = `uncertain`

### Supplied signs ###

Clusters with `< >` indicate that these signs have been supplied in order to
make sense.

Collected in the feature **type** = `supplied`

### Members and embedding ###

The direct members of a cluster can be found by following the **sub** edges from
a cluster. They reach all outermost [*quads*](#quad) and [*signs*](#sign) that
belong to a cluster.

Clusters may lie embedded in each other. There are also **sub** edges from
clusters to embedded clusters.

Case
----

A numbered transcription line corresponds to a *case*. A sequence of
[*quads*](#quad) forms a case.

Cases represent rectangular blocks on a [*tablet*].

Those cases may be grouped into bigger *cases*, and ultimately they are grouped
in [*lines*](#line), based on their number.

All cases in a [*line*](#line) (see below) that start with the same number, form
a bigger *case*. The number itself is recorded in the feature **number**.

So cases with numbers `1a`, `1b`, and `2` form two [*lines*](#line): one with
number `1`, containing cases `1a` and `1b`, and one with number `2`, containing
just case `2`.

If the numbers show deeper hierarchy, we build up cases. Cases with numbers
`1a1`, `1a2`, `1b`, and `2` form (again) two lines. The line with number `1` has
two *cases*: one with number `1a`, containing cases `1a1` and `1a2`, and one
with number `1b`, containing just case `1b`.

If a [*line*](#line) is not subdivided in multiple cases, we still say that the
line contains one case.

This is an example *case*.

    1.b1. , (EN~a DU ZATU759)a

Note that the number is a hierarchical number, with alternating digits and
letters. We strip the `.`s. This is the number that is used to group the lines
into *cases*, see below.

Like the numbers of [*columns*](#column), *case* numbers may have a `'` at the
end. But unlike *column* numbers, there might be primes on individual parts of
the hierarchical number. In the presence of a prime anywhere, we add to the
[*line*](#line) a feature **prime** with value `1`. We do not strip any prime
from the number.

We store the full hierarchical number of the "terminal" *cases* (the ones
without sub-*cases*) in the feature **fullNumber**.

We store the individual number parts in the feature **number**. These are the
parts that distinguish the sub-*cases* within their containing *case*.

### Bad numbering ###

Sometimes a column is badly numbered. These are the things that might occur:

1.  multiple lines with the same number
2.  numbers in the wrong order
3.  lines with a number of which an initial part is also the number of an other
    line
4.  lines without numbers

Examples can be found in the
[diagnostics](https://github.com/Dans-labs/Nino-cunei/blob/master/reports/diagnostics.tsv)
produced by the conversion
[tfFromAtf](https://github.com/Dans-labs/Nino-cunei/blob/master/programs/tfFromAtf.tsv)

This is how the conversion responds to these issues:

In cases **1** and **2** the column in question will get a feature
**badNumbering** with value `1` or `2`, depending on whether case 1 or 2
applies.

In both cases, we do not construe [*lines*](#line) and cases out of the
numbering. Instead, all lines in the column will get for **number** a simple
sequence number that reflects their position in the column. And the number found
in the transcription will be stored in the feature **fullNumber**, as usual.

Case **3** exhibits a pattern of numbers such as 1, 1a, 1b in one column. One
would expect either 1, or 1a with 1b. If we have all three then case 1 is both a
terminal case and a case with subcases. We deal with it by making an extra
terminal case under 1, indicated with the empty number, which holds the material
of transcription line 1. So line 1 hase three cases: case `''`, case `a`, and
case `b`.

Case **4** occurs very rarely. We insert a number, obtained by incrementing the
previous line number in the column. If there is no such one, we take `1`. If the
previous number is 1b3A, we pick 1b3B. The new number ends up in the
**fullNumber** feature. However, we record the fact that this is not the number
found in the transcription by filling the feature **origNumber** with the value
`''` (the empty string).

This measure may trigger case **1**. Then we fall back to the way we deal with
that case.

The rationale for these measures is:

*   we do not want to discard material if numbers are wrong;
*   we want to rescue as much normal processing of lines and cases as possible;
*   we want to leave traces if we override the transcription;
*   we generate diagnostics that help to correct the sources.

### Crossrefs ###

Lines can be cross-referenced with lines on other tablets (not necessarily
within this corpus). A cross-reference consists of a line after the source line:

    1.  1(N01) , |1(N57).SZUBUR|
    >> P000014 oi2

    1'. [1(N01)] , [...]
    >>Q000023 026 ?

This means that line `1.` corresponds to line `oi2` in text `P000014` and that
line `1'.` corresponds to line `026` in text `Q000023`, although with
uncertainty.

We collect this information in the feature **crossref**, with value
`P000014.oi2` and `Q000023.026:?` respectively.

If there are several cross-references from the same *case* line, we collect them
in a comma separated list.

Comments
--------

Lines starting with `$` or `#` are *comments* to the current object
([*tablet*](#tablet), [*face*](#face), [*column*](#column), or [*line*](#line).

Lines starting with `@object` are comments to the current object.

    &P002718 = ATU 3, pl. 078, W 17729,cn+
    #version: 0.1
    #atf: lang qpc

and

    4.  1(N01) , [...]
    $ rest broken
    @column 3
    $ beginning broken

Comments are a separate node type. They get one slot with an empty grapheme to
anchor them to the text.

The type of comment is stored in the feature **type**:

transcription | **type** feature | description
------------- | ---------------- | -----------
`$` | `ruling` | a rule like marking on the tablet
`#` | `meta` | metadata
`@object` | `object` | object description

The line number and the text on the line are collected in features **srcLnNum**
and **srcLn** respectively.

There is also an edge feature **comments**, with edges going from the object to
its *comments* nodes.

By using

    E.comments.f(t)

we get the list of *comments* nodes to tablet node `t` in a straigthforward way;
this list does not contain the *comments* to the *faces*, *columns*, *lines* of
the *tablet*.

Likewise, by using

    E.comments.t(c)

we get the object to which *comment* `c` is targeted.

Line
----

A node of type *line* corresponds to all [*cases*](#case) whose numbers start
with the same decimal number.

**This node type is section level 3.**

If we encounter a line without a preceding [*column*](#column) specifier we
proceed as if we have seen a `@column 0`.

The **number** of a line is always a single number, without a hierarchical
structure.

Column
------

[*Lines*](#line) are grouped into *columns*.

*Columns* are marked by lines like

    @column number

A node of type *column* corresponds to the material after the *column* specifier
and before the next next *column* specifier or the end of a [*face*](#face) or
[*tablet*](#tablet).

**This node type is section level 2.**

The number of a column is stored in the feature **number**. However, this number
is not suitable as a section number, because a *tablet* may have multiple faces
(which we do not take as a section level), and each of the faces restart the
*column* numbering.

We add a feature **fullNumber** to columns, filled with the type of the face
(see below) and the column **number**, separated by a `:`.

There might be a prime `'` after the number, but before the last `.` If present,
it indicates that the number does not count objects on the tablet in its
original state, but in its present state. If the tablet is damaged, material is
missing, and the missing items are not numbered.

In the presence of a prime, we add a feature **prime** with value `1` and we
remove the prime from the *column* number.

Face
----

[*Columns*](#column) are grouped into [*faces*](#face).

*Faces* are marked by lines like

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
before the next *face* specifier or the end of a [*tablet*](#tablet).

**This node type is not a section level!**

We make a feature **type** for this node type, which contains the name of the
*face*, e.g. `obverse`, `reverse`.

We also make a feature **identifier**, which contains the identifier if the
**type** is `surface` or `seal`.

`@seal` is never followed by linguistic content.

If there are columns outside a *face*, we act as if we have seen a `@noface`,
i.e. we insert a *face* with the name `noface`.

### fragment ###

There is another subdivision, very occasionally:

    @fragment identifier

This is really between [*tablet*](#tablet) and *face*. But it occurs only in one
*tablet*, which is too rare to merit a separate node type.

We make a feature **fragment**, which will be filled by the identifier of a
preceding `@fragment`.

Tablet
------

[*Faces*](#face) are grouped into *tablets*.

*Tablets* are marked by lines like

    @tablet

Sometimes this line sometimes missing. The surest sign of the beginning of a
*tablet* is a line like

    &P002174 = ATU 6, pl. 48, W 14731,?4

Here we collect `P002174` as the **catalogId** of the *tablet*, and
`ATU 6, pl. 48, W 14731,?4` as the tablet **name**.

We also add the name of the corpus as a feature **period**.

A node of type *tablet* corresponds to the material after a *tablet* specifier
and before the next *tablet* specifier.

**This node type is section level 1.**

Our corpora are just sets of *tablets*. The position of a particular tablet in
the whole set is not meaningful. The main identification of tablets is by their
**catalogId** (in this case *P number*), not by any sequence number within the
corpus.

Subsequent lines starting with `#` or `@object` are treated as
[*comments*](#comment).

Empty objects
=============

If objects such as [*tablets*](#tablet), [*faces*](#face), [*columns*](#column),
[*lines*](#line), and [*comments*](#comment) lack textual material, they will
not have slots. This is incompatible with the Text-Fabric model, where all nodes
must be anchored to the slots. We will take care that if textual material is
missing, we insert a special [*sign*](#sign). This is a sign with **grapheme** =
`''`, the empty string.

Not that quite a few of the empty [*signs*](#sign) we thus create, are for
[*comments*](#comment). These are the only [*signs*](#sign) that do not occur
within [*quads*](#quad).

Warning
=======

In order to produce transcribed text you cannot rely on features of slots alone.
Every node type introduces bits of syntax in the transcription.
