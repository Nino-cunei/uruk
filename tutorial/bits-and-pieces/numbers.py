# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + [markdown] toc=true
# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc" style="margin-top: 1em;"><ul class="toc-item"><li><span><a href="#Start-up" data-toc-modified-id="Start-up-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Start up</a></span><ul class="toc-item"><li><span><a data-toc-modified-id="obverse-1.1"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>obverse</a></span></li><li><span><a data-toc-modified-id="reverse-1.2"><span class="toc-item-num">1.2&nbsp;&nbsp;</span>reverse</a></span></li><li><span><a data-toc-modified-id="obverse-1.3"><span class="toc-item-num">1.3&nbsp;&nbsp;</span>obverse</a></span></li><li><span><a data-toc-modified-id="reverse-1.4"><span class="toc-item-num">1.4&nbsp;&nbsp;</span>reverse</a></span></li><li><span><a data-toc-modified-id="obverse-1.5"><span class="toc-item-num">1.5&nbsp;&nbsp;</span>obverse</a></span></li><li><span><a data-toc-modified-id="reverse-1.6"><span class="toc-item-num">1.6&nbsp;&nbsp;</span>reverse</a></span></li></ul></li></ul></div>
# -

# <img src="images/ninologo.png" align="right" width="100"/>
# <img src="images/tf.png" align="right" width="100"/>
#
#
# # Numbers

# ## Start up
#
# We import the Python modules we need.

# %load_ext autoreload
# %autoreload 2

# +
import os
import collections
from IPython.display import display, Markdown

from tf.extra.cunei import Cunei

# -

LOC = ("~/github", "Nino-cunei/uruk", "numbers")
A = Cunei(*LOC)
A.api.makeAvailableIn(globals())


def dm(markdown):
    display(Markdown(markdown))


# # Using Text-Fabric Search
#
# Text-Fabric has a [search](https://annotation.github.io/text-fabric/tf/about/searchusage.html)
# facility, by which you can avoid a lot of programming. Let's get all the shinPP numerals on a reverse face.

# +
pNums = """
    P005381
    P005447
    P005448
""".strip().split()

pNumPat = "|".join(pNums)

# +
shinPP = dict(
    N41=0.2,
    N04=1,
    N19=6,
    N46=60,
    N36=180,
    N49=1800,
)

shinPPPat = "|".join(shinPP)
# -

# We query for shinPP numerals on the faces of selected tablets.
# The result of the query is a list of tuples `(t, f, s)` consisting of
# a tablet node, a face node and a sign node, which is a shinPP numeral.

query = f"""
tablet catalogId={pNumPat}
    face
        sign type=numeral grapheme={shinPPPat}
"""

results = list(S.search(query))
len(results)

# We have found 20 numerals.
# We group the results by tablet and by face.

numerals = {}
for (tablet, face, sign) in results:
    numerals.setdefault(tablet, {}).setdefault(face, []).append(sign)

# We show the tablets, the shinPP numerals per face, and we add up the numerals per face.

for (tablet, faces) in numerals.items():
    dm("---\n")
    display(A.lineart(tablet, withCaption="top", width="200"))
    for (face, signs) in faces.items():
        dm(f"### {F.type.v(face)}")
        distinctSigns = {}
        for s in signs:
            distinctSigns.setdefault(A.atfFromSign(s), []).append(s)
        display(A.lineart(distinctSigns))
        total = 0
        for (signAtf, signs) in distinctSigns.items():
            # note that all signs for the same signAtf have the same grapheme and repeat
            value = 0
            for s in signs:
                value += F.repeat.v(s) * shinPP[F.grapheme.v(s)]
            total += value
            amount = len(signs)
            shinPPval = shinPP[F.grapheme.v(signs[0])]
            repeat = F.repeat.v(signs[0])
            print(f"{amount} x {signAtf} = {amount} x {repeat} x {shinPPval} = {value}")
        dm(f"**total** = **{total}**")

# # Frequency of Quads

# We count the number of quads, according to their ATF string.

quadFreqs = collections.Counter()
for q in F.otype.s("quad"):
    quadFreqs[A.atfFromQuad(q)] += 1

for qAtf in quadFreqs:
    if "GISZ" in qAtf:
        print(f"{quadFreqs[qAtf]:>4} x {qAtf}")

# Frequency of a particular quad:

pQuad = "GI4~a"
print(f"The frequency of {pQuad} is {quadFreqs[pQuad]}")

# Not what you expected? Let's broaden the question

for qAtf in quadFreqs:
    if "GI4" in qAtf:
        print(f"{quadFreqs[qAtf]:>4} x {qAtf}")

# Ah, `GI4~a` is a single sign, not a complex quad. Quads are by definition complex.
#
# That's why you want signs and quads in one table. Let's do it.

# +
quadSignFreqs = collections.Counter()
quadSignTypes = {"quad", "sign"}

for n in N():
    nType = F.otype.v(n)
    if nType not in quadSignTypes:
        continue
    atf = A.atfFromQuad(n) if nType == "quad" else A.atfFromSign(n)
    quadSignFreqs[atf] += 1
for qsAtf in quadSignFreqs:
    if "GISZ" in qsAtf or "GI4" in qsAtf:
        print(f"{quadSignFreqs[qsAtf]:>4} x {qsAtf}")
# -

pQuad = "GI4~a"
print(f"The frequency of {pQuad} is {quadSignFreqs[pQuad]}")

# # Write frequencies

# You can make an output directory by hand, but we do it programmatically.

reportDir = "reports"
os.makedirs(reportDir, exist_ok=True)


def writeFreqs(fileName, data, dataName):
    print(f"There are {len(data)} {dataName}s")

    for (sortName, sortKey) in (
        ("alpha", lambda x: (x[0], -x[1])),
        ("freq", lambda x: (-x[1], x[0])),
    ):
        with open(f"{reportDir}/{fileName}-{sortName}.txt", "w") as fh:
            for (item, freq) in sorted(data.items(), key=sortKey):
                if item != "":
                    fh.write(f"{freq:>5} x {item}\n")


writeFreqs("quad-signs", quadSignFreqs, "quad/sign")

# # Grabbing subcases
#
# How can we quickly grab cases at a certain level?
# There is a short answer and a long answer.
#
# Here is the short anwer: a new `A`-utility function that does it for you.

subcases = A.casesByLevel(2, terminal=True)
len(subcases)

# A basic check: which numbers do we get?

caseNumbers = collections.Counter()
for s in subcases:
    caseNumbers[F.number.v(s)] += 1
caseNumbers

# This is what happens under the hood.
#
# The next query picks every line in which there is a case in which there is a case
# such that the case is a direct child of the line and the subcase is a direct child of the case.
#
# This is what the `sub` edge is for. A case containing another case is very liberal. Cases not only contain
# their subcases, but also their subsubcases and so on.
# Using `sub` brings is close to what we want.

query = """
l:line
    w1:case
        w2:case
l -sub> w1
w1 -sub> w2
"""

results = list(S.search(query))
len(results)

# We still may have too much. Subcases may contain cases themselves, and in that case they do not correspond to a single line in the
# transcription.
# If you want only subcases that are terminal cases, you have to filter the results by means of an extra line of code.
#
# A case is terminal if it has a feature `terminal` (with value `1`).

subcases = [subcase for (line, case, subcase) in results if F.terminal.v(subcase)]
len(subcases)

# Let's just check whether the subcases have reasonable line numbers.

caseNumbers = collections.Counter()
for subcase in subcases:
    cn = F.number.v(subcase)
    if cn:
        caseNumbers[cn] += 1

caseNumbers

# In order to get cases at deeper levels, we need to compose a query that is dependent on
# the given depth. That is exactly what the `A.casesByLevel` function does.

# # Displaying subcases
#
# We show the ATF of nested subcases, together with their location in the corpus.

# We pick a deep level of cases, in order to make an inventory of the signs involved.

# +
sublevel4Nodes = A.casesByLevel(4, terminal=True)

for node in sublevel4Nodes:
    (pNum, column, lineNum) = T.sectionFromNode(node)
    srcLn = F.srcLn.v(node)
    print(f"{pNum}:{column}:{lineNum} = {srcLn}")
# -

# We collect all sign nodes in these cases into a list.

sublevel4Signs = []
for c4 in sublevel4Nodes:
    for sign in L.d(c4, otype="sign"):
        sublevel4Signs.append(sign)

# We count the signs occurring in these cases by their full ATF representation.

signs4count = collections.Counter()
for s in sublevel4Signs:
    signs4count[A.atfFromSign(s)] += 1

# We print the counts, first sorted by atf representation.

for (sign, amount) in sorted(signs4count.items()):
    print(f"{amount:>4} x {sign}")

# and now the same list, sorted by frequency.

for (sign, amount) in sorted(
    signs4count.items(),
    key=lambda x: (-x[1], x[0]),
):
    print(f"{amount:>4} x {sign}")

# # TILL SO FAR
# Below are ways to classify tablets as to what number systems are present on them.
# This I did earlier.

# Specification of the Shin systems: just the bare minimum of info.

numberSystems = dict(
    shinP=(40, 3, 18, 24, 45),
    shinPP=(4, 19, 36, 41, 46, 49),
    shinS=(25, 27, 28, 42, 5, 20, 47, 37),
)

# We turn the numbers into numeral graphemes:

# +
systems = {}

for (shin, numbers) in numberSystems.items():
    systems[shin] = {f"N{n:>02}" for n in numbers}
# -

# Reality check

systems

# We also want the opposite: given a numeral, which system is it?

# +
numeralMap = {}

for (shin, numerals) in systems.items():
    for n in numerals:
        if n in numeralMap:
            dm(f"**warning:** Numeral {n} in {shin} was already in {numeralMap[n]}")
        numeralMap[n] = shin

numeralMap
# -

# Exercise:
#
# For each tablet, add three properties: hasShinP, hasShinPP, hasShinS.
# They will be True if and only if the tablet has a numeral in that category.
# Even better, instead of True or False, we let them record how many numerals in that set they have.

# +
tabletNumerics = collections.defaultdict(collections.Counter)

for tablet in F.otype.s("tablet"):
    pNum = F.catalogId.v(tablet)
    for sign in L.d(tablet, otype="sign"):
        if F.type.v(sign) == "numeral":
            numeral = F.grapheme.v(sign)
            system = numeralMap.get(numeral, None)
            if system is not None:
                tabletNumerics[pNum][system] += 1
# -

# Now we write a csv file to the report directory, so that you can work with the data in Excel.
#
# We show the first few lines in the notebook

# +
filePath = f"{A.reportDir}/tabletNumerics.tsv"
lines = []
systemNames = sorted(systems)
fieldNames = "\t".join(systemNames)
for pNum in sorted(tabletNumerics):
    data = tabletNumerics[pNum]
    values = "\t".join(str(data[s]) for s in systemNames)
    lines.append(f"{pNum}\t{values}\n")
with open(filePath, "w") as fh:
    fh.write(f"tablet\t{fieldNames}\n")
    fh.write("".join(lines))

print("".join(lines[0:10]))
