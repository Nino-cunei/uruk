nino-cunei
==========

<img src="programs/images/quad.png" align="left" width="40%"/>
<img src="programs/images/tf.png" align="right" width="30%"/>

[source of image](https://814eportfolios11.wikispaces.com/Kim814)

Cuneiform corpora in Text-Fabric

Sources
=======

We have taken transcriptions from [CDLI](https://cdli.ucla.edu), the Cuneiform
Digital Library Initiative.

On the [search page](https://cdli.ucla.edu/search/search.php) we entered under
*Chronology - period*: `Uruk III` and `Uruk IV` respectively. On the results
page, we have chosen `Download transliterations`. Below we list the download
links per corpus.

In this repo we convert the following corpora to Text-Fabric:

*   Uruk III -
    [4882 texts](https://cdli.ucla.edu/search/download_data_new.php?data_type=just_transliteration)
*   Uruk IV -
    [1861 texts](https://cdli.ucla.edu/search/download_data_new.php?data_type=just_transliteration)

We have a [specification](docs/transcription.md) of the transcription format and
how we model the text in Text-Fabric.

Status
======

This is **work in progress!**

*   2018-02-09 Conversion coding has just started. We only parse supra-line units.
    We do not yet generate any Text-Fabric data. The sub-line parsing will be the
    most work.

Authors
=======

This repo is joint work of

*   [Justin Cale Johnson](https://www.universiteitleiden.nl/en/staffmembers/cale-johnson#tab-1)
    at
    [Assyriology, University Leiden](https://www.universiteitleiden.nl/en/humanities/institute-for-area-studies/assyriology)
    and [NINO](http://www.nino-leiden.nl) library.
*   [Dirk Roorda](https://www.linkedin.com/in/dirkroorda/) at
    [DANS](https://www.dans.knaw.nl)
