LIMIT = 20

FLAGS = (
    ('damage', '#'),
    ('remarkable', '!'),
    ('written', ('!(', ')')),
    ('uncertain', '?'),
)

OUTER_QUAD_TYPES = {'sign', 'quad'}

CLUSTER_BEGIN = {'[': ']', '<': '>', '(': ')'}
CLUSTER_END = {y: x for (x, y) in CLUSTER_BEGIN.items()}
CLUSTER_KIND = {'[': 'uncertain', '(': 'properName', '<': 'supplied'}
CLUSTER_BRACKETS = dict((name, (bOpen, CLUSTER_BEGIN[bOpen]))
                        for (bOpen, name) in CLUSTER_KIND.items())


class Cunei(object):
    def __init__(self, api):
        self.api = api

    def atfFromSign(self, n, flags=False):
        F = self.api.F
        Fs = self.api.Fs
        if F.otype.v(n) != 'sign':
            return '«no sign»'

        grapheme = F.grapheme.v(n)
        if grapheme == '…':
            grapheme = '...'
        prime = "'" if F.prime.v(n) else ''

        variantValue = F.variant.v(n)
        variant = f'~{variantValue}' if variantValue else ''

        modifierValue = F.modifier.v(n)
        modifier = f'@{modifierValue}' if modifierValue else ''
        modifierInnerValue = F.modifierInner.v(n)
        modifierInner = f'@{modifierInnerValue}' if modifierInnerValue else ''

        modifierFirst = F.modifierFirst.v(n)

        repeat = F.repeat.v(n)
        if repeat is None:
            varmod = (
                f'{modifier}{variant}'
                if modifierFirst else f'{variant}{modifier}'
            )
            result = f'{grapheme}{prime}{varmod}'
        else:
            if repeat == -1:
                repeat = 'N'
            varmod = (
                f'{modifierInner}{variant}'
                if modifierFirst else f'{variant}{modifierInner}'
            )
            result = f'{repeat}({grapheme}{prime}{varmod}){modifier}'

        if flags:
            for (flag, char) in FLAGS:
                value = Fs(flag).v(n)
                if value:
                    if type(char) is tuple:
                        result += f'{char[0]}{value}{char[1]}'
                    else:
                        result += char

        return result

    def atfFromQuad(self, n, flags=False, outer=True):
        api = self.api
        E = api.E
        F = api.F
        Fs = api.Fs
        if F.otype.v(n) != 'quad':
            return '«no quad»'

        children = E.sub.f(n)
        if not children or len(children) < 2:
            return f'«quad with less than two sub-quads»'
        result = ''
        for child in children:
            nextChildren = E.op.f(child)
            if nextChildren:
                op = nextChildren[0][1]
            else:
                op = ''
            childType = F.otype.v(child)

            thisResult = (
                self.atfFromQuad(child, flags=flags, outer=False) if
                childType == 'quad' else self.atfFromSign(child, flags=flags)
            )
            result += f'{thisResult}{op}'

        variant = F.variantOuter.v(n)
        variantStr = f'~{variant}' if variant else ''

        flagStr = ''
        if flags:
            for (flag, char) in FLAGS:
                value = Fs(flag).v(n)
                if value:
                    if type(char) is tuple:
                        flagStr += f'{char[0]}{value}{char[1]}'
                    else:
                        flagStr += char

        if variant:
            if flagStr:
                if outer:
                    result = f'|({result}){variantStr}|{flagStr}'
                else:
                    result = f'(({result}){variantStr}){flagStr}'
            else:
                if outer:
                    result = f'|({result}){variantStr}|'
                else:
                    result = f'({result}){variantStr}'
        else:
            if flagStr:
                if outer:
                    result = f'|{result}|{flagStr}'
                else:
                    result = f'({result}){flagStr}'
            else:
                if outer:
                    result = f'|{result}|'
                else:
                    result = f'({result})'

        return result

    def atfFromOuterQuad(self, n, flags=False):
        api = self.api
        F = api.F
        nodeType = F.otype.v(n)
        if nodeType == 'sign':
            return self.atfFromSign(n, flags=flags)
        elif nodeType == 'quad':
            return self.atfFromQuad(n, flags=flags, outer=True)
        else:
            return '«no outer quad»'

    def atfFromCluster(self, n, seen=None):
        api = self.api
        F = api.F
        E = api.E
        if F.otype.v(n) != 'cluster':
            return '«no cluster»'

        typ = F.type.v(n)
        (bOpen, bClose) = CLUSTER_BRACKETS[typ]
        if bClose == ')':
            bClose = ')a'
        children = api.sortNodes(E.sub.f(n))

        if seen is None:
            seen = set()
        result = []
        for child in children:
            if child in seen:
                continue
            childType = F.otype.v(child)

            thisResult = (
                self.atfFromCluster(child, seen=seen) if childType == 'cluster'
                else self.atfFromQuad(child, flags=True) if childType == 'quad'
                else self.atfFromSign(child, flags=True)
                if childType == 'sign' else None
            )
            seen.add(child)
            if thisResult is None:
                print(
                    f'TF: child of cluster has type {childType}:'
                    ' should not happen'
                )
            result.append(thisResult)
        return f'{bOpen}{" ".join(result)}{bClose}'

    def getOuterQuads(self, n):
        api = self.api
        F = api.F
        E = api.E
        L = api.L
        return [
            quad for quad in L.d(n)
            if (
                F.otype.v(quad) in OUTER_QUAD_TYPES and
                all(F.otype.v(parent) != 'quad' for parent in E.sub.t(quad))
            )
        ]
