import re


def error(key, p, curTablet):
    errors.setdefault(key, []).append(
        '{}.{} ({}): {}'.format(
            p[0], p[1], curTablet.get('catalogId', ''), p[2]
        )
    )


flagsPat = re.compile('^(.*)([#?]|(?:[!]\([^)]*\)))$')
modifierPat = re.compile('^(.*)@(.)$')

MODIFIERS = set(
    '''
    c
    f
    g
    s
    t
    n
    z
    k
    r
    h
'''.strip().split()
)


def parseQuad(quad, p, curTablet):
    base = quad
    flags = {}
    modifiers = {}
    stop = False
    # modifiers
    while base != '' and not stop:
        splits = modifierPat.findall(base)
        if not splits:
            stop = True
        else:
            (base, modStr) = splits[0]
            if modStr not in MODIFIERS:
                error(f'Modifier "@{modStr}" unknown', p, curTablet)
            else:
                if modStr in modifiers:
                    error(f'Modifier "@{modStr}" repeated', p, curTablet)
                modifiers[modStr] = 1

    # flags
    stop = False
    while base != '' and not stop:
        splits = flagsPat.findall(base)
        if not splits:
            stop = True
        else:
            (base, flagStr) = splits[0]
            if flagStr == '#':
                if 'damage' in flags:
                    error(f'Flag "#" repeated', p, curTablet)
                flags['damage'] = 1
            elif flagStr == '?':
                if 'uncertain' in flags:
                    error(f'Flag "?" repeated', p, curTablet)
                flags['uncertain'] = 1
            elif flagStr.startswith('!'):
                if 'written' in flags:
                    error(f'Flag "!()" repeated', p, curTablet)
                flags['written'] = flagStr[2:-1]
    if base == '':
        error('Empty quad', p, curTablet)
    else:
        if base[0] == '|':
            if len(base) == 1:
                error('Empty quad "|"', p, curTablet)
                base = ''
            else:
                if base[-1] == '|':
                    if len(base) == 2:
                        error('Empty quad "||"', p, curTablet)
                        base = ''
                    else:
                        base = base[1:-1]
                else:
                    error('Quad not terminated with "|"', p, curTablet)
                    base = base[1:]
        else:
            if base[-1] == '|':
                error('Quad does not start with "|"', p, curTablet)
                base = base[0:-1]
    struct = quadStructure(base, p, curTablet)
    result = {'quad': struct}
    if flags:
        result['flags'] = flags
    if modifiers:
        result['modifiers'] = modifiers
    return result


def parseTerminal(string):
    return [] if string == '' else [string]


def parseBrackets(string, fromPos, wantClose):
    result = []
    errors = []
    stop = False
    ls = len(string)
    while fromPos < ls and not stop:
        firstOpen = string.find('(', fromPos)
        firstClose = string.find(')', fromPos)
        if firstOpen == -1:
            firstOpen = ls
        if firstClose == -1:
            firstClose = ls
        firstBracket = min((firstOpen, firstClose))
        if firstBracket == ls:
            before = string[fromPos:]
            bracket = ''
        else:
            before = string[fromPos:firstBracket]
            bracket = string[firstBracket]
        result.extend(parseTerminal(before))
        if bracket == ')':
            if wantClose:
                stop = True
                wantClose = False
            else:
                pb = string[0:firstBracket]
                pB = string[firstBracket]
                pa = string[firstBracket + 1:]
                errors.append(f'Extra ")" in "{pb}▶{pB}◀{pa}"')
            fromPos = firstBracket + 1
        elif bracket == '(':
            (subResult, fromPos, subErrors) = parseBrackets(
                string,
                firstBracket + 1,
                True,
            )
            result.append(subResult)
            errors.extend(subErrors)
        else:
            fromPos = ls
    if wantClose:
        if fromPos >= ls:
            errors.append(f'Missing ")" after "{string}▲"')
        elif string[fromPos] != ')':
            errors.append(
                f'Missing ")" in "{string[0:fromPos]}▲{string[fromPos:]}"',
            )
        else:
            fromPos += 1
    return (result, fromPos, errors)


def quadStructure(string, p, curTablet):
    (result, restPos, errors) = parseBrackets(string, 0, False)
    if restPos < len(string):
        pb = string[0:restPos]
        pa = string[restPos:]
        errors.append(f'Trailing characters in "{pb}▲{pa}"')
    if errors:
        errorStr = '\n\t\t'.join(errors)
        error(f'bracket error in quad:\n\t\t{errorStr}', p, curTablet or {})
    return result


for test in '''
    |AB~bxSZA3~a1|#?
'''.strip().split():
    print(f'INPUT = "{test}"')
    errors = {}
    result = parseQuad(test, (1, 1, 1), {'catalogId': 'xx'})
    if errors:
        for (kind, msgs) in sorted(errors.items(), key=lambda x: x[0]):
            print(f'\t{kind}')
            for msg in msgs:
                print(f'\t\t{msg}')
    print(result)
    print('------------------------------------')
