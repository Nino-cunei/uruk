<img src="images/logo.png" align="left"/>
<img src="images/ninologo.png" align="right" width="20%"/>

The Uruk corpus
==============================

This repo is about the digital processing of the transliterations of
proto-cuneiform tablets from the Uruk IV-III periods.

Cuneiform tablets
=================

Cuneiform tablets have been photographed, drawn as lineart, and transliterated
in [ATF](http://oracc.museum.upenn.edu/doc/help/editinginatf/cdliatf/index.html)
files, in which the marks on a tablet are represented by ascii characters.

While the ATF descriptions preserve an awesome amount of precise information
about the marks that are visible in the clay and their spatial structure, it is
not easy to process that information. Simple things are hard: counting,
aggregating, let alone higher level tasks such as clustering, colocation, and
other statistical operations.

That is why we have converted the transliterations to an other format,
Text-Fabric, which is optimized for processing, adding data and sharing it.

We also have drawn in photos and lineart, which can be used while computing,
especially when done in Jupyter notebooks. Done this way, computer analysis
turns into rich computational narratives.

Corpus
------

We have chosen the
[Uruk-IV/III periods](http://cdli.ox.ac.uk/wiki/doku.php?id=proto-cuneiform)
(4000-3100 BC) as a starting corpus for testing our approach. This is
*proto-cuneiform* corpus of ca. 6000 tablets.

The second corpus we have brought into Text-Fabric is the 
[Old Babylonian Letters](https://github.com/Nino-cunei/oldbabylonian/blob/master/docs/about.md).

Provenance
----------

We have downloaded transliterations and images from the **Cuneiform Digital
Library Initiative** [CDLI](https://cdli.ucla.edu). They have a rich source of
data, available to the public, visible on their website, and large portions are
conveniently downloadable. We are indebted to the creators and maintainers of
the CDLI website.

### Transliterations

On the [search page](https://cdli.ucla.edu/search/search.php) we entered under
*Chronology - period*: `Uruk IV` and `Uruk III` respectively. On the results
page, we have chosen `Download all text`. Below we list the download
links per corpus.

In this repo we convert the following corpora to Text-Fabric:

*   Uruk IV -
    [1861 texts](https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&requestFrom=Search&PrimaryPublication=&Author=&PublicationDate=&SecondaryPublication=&Collection=&AccessionNumber=&MuseumNumber=&Provenience=&ExcavationNumber=&Period=uruk+iv&DatesReferenced=&ObjectType=&ObjectRemarks=&Material=&TextSearch=&TranslationSearch=&CommentSearch=&StructureSearch=&Language=&Genre=&SubGenre=&CompositeNumber=&SealID=&ObjectID=&ATFSource=&CatalogueSource=&TranslationSource=)
*   Uruk III -
    [4882 texts](https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&requestFrom=Search&PrimaryPublication=&Author=&PublicationDate=&SecondaryPublication=&Collection=&AccessionNumber=&MuseumNumber=&Provenience=&ExcavationNumber=&Period=uruk+iii&DatesReferenced=&ObjectType=&ObjectRemarks=&Material=&TextSearch=&TranslationSearch=&CommentSearch=&StructureSearch=&Language=&Genre=&SubGenre=&CompositeNumber=&SealID=&ObjectID=&ATFSource=&CatalogueSource=&TranslationSource=)

Note that these "corpora" are merely the results of a query by period. They are
not corpora in the sense of an identified body of texts in which each individual
text occupies a fixed position in the sequence.

The downloaded files contain metadata and transliterations.
We have extracted the transliterations to separate files.
We only use the *excavation number* from the metadata.

We have a [specification](transcription.md) of the transcription format and
how we model the text in Text-Fabric.

We have checked the conversion from the ATF transliterations to Text-Fabric
extensively. Cruelly, you might say. An account of the checking that we
performed is in the
[checks](http://nbviewer.jupyter.org/github/Nino-cunei/uruk/blob/master/programs/checks.ipynb)
notebook.

### Images

We have obtained three image sets from CDLI:

*   photos of tablets;
*   lineart images of tablets;
*   lineart images of ideographs;

For details, see [images](images.md).

