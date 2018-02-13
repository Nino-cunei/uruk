errors = {}


def error(key, p, curTablet):
    errors.setdefault(key, []).append(
        '{}.{} ({}): {}'.format(
            p[0], p[1], curTablet.get('catalogId', ''), p[2]
        )
    )


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


for test in [''] + '''
    ()
    (
    )
    )(
    ((
    ))
    (())
    aa
    (aa)
    (aa)bb
    (aa)(bb)
    (aa)cc(bb)
    ((aa)cc)bb
    (((aa)cc)bb)
    (((aa)cc)bb))
'''.strip().split():
    print(f'INPUT = "{test}"')
    errors = {}
    result = structure(test, (1, 1, 1), {'catalogId': 'xx'})
    if errors:
        for (kind, msgs) in sorted(errors.items(), key=lambda x: x[0]):
            print(f'\t{kind}')
            for msg in msgs:
                print(f'\t\t{msg}')
    print(result)
    print('------------------------------------')
