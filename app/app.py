import types
from tf.advanced.helpers import dh
from tf.advanced.find import loadModule
from tf.advanced.app import App


def transform_prime(app, n, p):
    return ("'" * int(p)) if p else ""


def transform_ctype(app, n, t):
    if t == "uncertain":
        return "?"
    elif t == "properName":
        return "="
    elif t == "supplied":
        return "&gt;"
    else:
        return ""


def transform_atf(app, n, a):
    return app.atfFromSign(n, flags=True)


class TfApp(App):
    def __init__(app, *args, silent=False, **kwargs):
        app.transform_ctype = types.MethodType(transform_ctype, app)
        app.transform_prime = types.MethodType(transform_prime, app)
        app.transform_atf = types.MethodType(transform_atf, app)

        atf = loadModule("atf", *args)
        atf.atfApi(app)
        app.atf = atf
        super().__init__(*args, silent=silent, **kwargs)
        app.image = loadModule("image", *args)

        app.image.getImagery(app, silent, checkout=kwargs.get("checkout", ""))

        app.reinit()

    def reinit(app):
        customMethods = app.customMethods

        customMethods.afterChild.clear()
        customMethods.afterChild.update(quad=app.getOp)
        customMethods.plainCustom.clear()
        customMethods.plainCustom.update(
            sign=app.plainAtfType, quad=app.plainAtfType, cluster=app.plainAtfType,
        )
        customMethods.prettyCustom.clear()
        customMethods.prettyCustom.update(
            case=app.caseDir, cluster=app.clusterBoundaries, comments=app.commentsCls
        )

    def cdli(app, n, linkText=None, asString=False):
        (nType, objectType, identifier) = app.image.imageCls(app, n)
        if linkText is None:
            linkText = identifier
        result = app.image.wrapLink(linkText, objectType, "main", identifier)
        if asString:
            return result
        else:
            dh(result)

    # PRETTY HELPERS

    def getGraphics(app, isPretty, n, nType, outer):
        api = app.api
        F = api.F
        E = api.E

        result = ""

        isOuter = outer or (all(F.otype.v(parent) != "quad" for parent in E.sub.t(n)))
        if isOuter:
            width = "2em" if nType == "sign" else "4em"
            height = "4em" if nType == "quad" else "6em"
            theGraphics = app.image.getImages(
                app,
                n,
                kind="lineart",
                width=width,
                height=height,
                _asString=True,
                withCaption=False,
                warning=False,
            )
            if theGraphics:
                result = f"<div>{theGraphics}</div>" if isPretty else f" {theGraphics}"

        return result

    def lineart(app, ns, key=None, asLink=False, withCaption=None, **options):
        return app.image.getImages(
            app,
            ns,
            kind="lineart",
            key=key,
            asLink=asLink,
            withCaption=withCaption,
            **options,
        )

    def photo(app, ns, key=None, asLink=False, withCaption=None, **options):
        return app.image.getImages(
            app,
            ns,
            kind="photo",
            key=key,
            asLink=asLink,
            withCaption=withCaption,
            **options,
        )

    def imagery(app, objectType, kind):
        return set(app._imagery.get(objectType, {}).get(kind, {}))
