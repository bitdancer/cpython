"""Support for Parameterized Tests"""

import collections
from functools import wraps
from string import Formatter


class SafeFormatter(Formatter):

    """Formatter equivalent of string.Template safe_substitute.

    >>> SafeFormatter().format('{a} {b!r}', a=1)
    1 {b!r}
    """

    def format(self, format_string, *args, **kw):
        self.args = args
        self.kw = kw
        return super().format(format_string, *args, **kw)

    def parse(self, format_string):
        for text, varname, spec, conv in super().parse(format_string):
            if varname and varname not in self.kw:
                spec = ':' + spec if spec else ''
                conv = '!' + conv if conv else ''
                text = text + '{' + varname + spec + conv + '}'
                varname, spec, conv = None, None, None
            yield text, varname, spec, conv

safe_format = SafeFormatter().format

def _fmt(fmtfunc, obj, subs):
    if hasattr(obj, 'format'):
        return safe_format(obj, **subs)
    if hasattr(obj, 'items'):
        return type(obj)({k: fmtfunc(v, subs) for k, v in obj.items()})
    try:
        i = iter(obj)
    except TypeError:
        return obj
    return type(obj)(fmtfunc(x, subs) for x in i)

def fmt(obj, subs):
    """Safely apply format to obj or any formatables it contains, using subs.

    If ob has a format attribute, call call a safe formatter on it, passing in
    subs as the dictionary of available values.  "safe formatting" means if a
    referenced variable does not exist, the format specification is left as is
    in the string, rather than an error being raised.  If obj has an items
    attribute, call its type with an argument list consisting of a mapping from
    the keys to the values returned by calling items, after applying the safe
    formatter to any values that have a format attribute, and return the
    resulting object.  If the obj is iterable, call its type with an argument
    consisting of a list of the results of iterating obj, after applying the
    safe formatter to any values that have a format attribute.

    """
    return _fmt(
        lambda obj, subs:
           safe_format(obj, **subs) if hasattr(obj, 'format') else obj,
        obj,
        subs,
        )

def fmtall(obj, subs):
    """Apply fmt to obj recursively."""
    return _fmt(fmtall, obj, subs)


class C:

    """Hold concrete *args and **kw for a callable.

    Store any positional arguments as a tuple in self.args, and any
    keyword arguments in as a dict in self.kw.

    Also called a "callspec".

    """

    def __init__(self, *args, **kw):
        self.args = args
        self.kw = kw

    def __call__(self, func):
        """Call func using the concrete arguments from self.args and self.kw"""
        return func(*self.args, **self.kw)

    def __eq__(self, other):
        """Instances are equal iff self.args and self.kw compare equal."""
        try:
            return self.args == other.args and self.kw == other.kw
        except AttributeError:
            return False

    def _repr(self, fname):
        args = ', '.join(repr(arg) for arg in self.args)
        kw = ', '.join(f'{k}={repr(v)}' for k, v in self.kw.items())
        return f"{fname}({', '.join(filter(None, (args, kw)))})"

    def __repr__(self):
        return self._repr(type(self).__name__)

    def repr_call(self, func):
        """Return the repr of the args and kw as if being passed to func"""
        return self._repr(func.__name__)

    def fmt(self, **subs):
        """Return a new C after applying fmt to the args and kw."""
        return C(*fmt(self.args, subs), **fmt(self.kw, subs))

    def fmtall(self, **subs):
        """Return a new C after applying fmtall to the args and kw."""
        return C(*fmtall(self.args, subs), **fmtall(self.kw, subs))


class Params(collections.UserDict):

    """A dictionary of callspecs.

    Restrict keys to valid identifiers.  Turn non-callspec values into single
    argument callspecs.

    """

    def __init__(self, *args, **kw):
        super().__init__()
        self.update(*args, **kw)

    def __repr__(self):
        items = ', '.join(f'{k}={repr(v)}' for k, v in self.items())
        return f'{type(self).__name__}({items})'

    def update(self, *args, **kw):
        for arg in args:
            if not isinstance(arg, self.__class__):
                raise TypeError(
                    f"Invalid argument {arg!r}, arguments"
                    f" must be of type {type(self).__name__},"
                    f" not {type(arg).__name__!r}"
                    )
            super().update(arg)
        super().update(kw)

    def __setitem__(self, name, value):
        if not name.isidentifier():
            raise ValueError(
                f"parameter names must be identifiers, {name!r} is invalid",
                )
        if name in self:
            raise ValueError(
                f"cannot add {name}={value!r}, a callspec with that name"
                f" already exists"
                )
        if not isinstance(value, C):
            value = C(value)
        super().__setitem__(name, value)


debug = False
_tupify = lambda x: x.items() if isinstance(x, Params) else [('', x)]
def _params_map(func, *, with_name=False, with_namelist=False, debug=False):
    if not callable(func):
        raise TypeError(
            f"argument must be callable, not {type(func).__name__!r}"
            )
    if with_name and with_namelist:
        raise ValueError("with_name and with_namelist cannot both be True")
    @wraps(func)
    def params_mapper(*args, **kw):
        if __debug__ and debug: print(f'flattening using {func.__name__}')
        if __debug__ and debug > 1: print(f'{args=} {kw=}')
        param_set = Params()
        for an, av in [t for a in [*args, Params(**kw)] for t in _tupify(a)]:
            if debug: print(f'{an=} {av=}')
            cs = C(*av.args, **av.kw) if isinstance(av, C) else C(av)
            if with_name:
                cs.args = (an, *cs.args)
            elif with_namelist:
                cs.args = (NameList(an), *cs.args)
            try:
                for n, v in cs(func):
                    try:
                        name = '__'.join(filter(None, (an, n)))
                    except Exception:
                        raise ValueError(f"Invalid label: {n!r}") from None
                    if __debug__ and debug: print(f'{n=} {v=} {name=}')
                    if not name:
                        raise ValueError('missing test label')
                    param_set[name] = v
            except Exception as ex:
                val = f'{an}={av!r}' if an else repr(av)
                raise ValueError(
                    f'{func.__name__} failed on {val}',
                    ) from ex
        return param_set
    return params_mapper

def params_map(*args, **kw):
    """Return decorator that flatmaps a function onto Params arguments.

    When called, expect any mix of objects, Params objects, and keyword
    arguments.  Treat any Params objects as a list of (key, value) pairs.
    Treat any non-Params positional arguments as ('', value) pairs.  Treat
    keyword arguments as (key, value) pairs.  Turn any value that is not a
    callspec into a single argument callspec.

    If params_map is called with with_name=True, insert the key part of the
    pair to the start of the callspec positional arguments.  If params_map is
    called with with_namelist=True, insert the result of calling NameList on
    the key part of the pair to the start of the callspec positional arguments.
    Raise an error if both with_name=True and with_namelist=True are
    specified.

    For each pair, call the wrapped function using the callspec.  The called
    function must return an iterator of (name, value) pairs.  If there was a
    non-null key in the original pair and the returned name is non-null, create
    a new name by joining the two with '__'.  Otherwise use whichever is
    non-null as the name.  If both are null, raise an error.

    Return a Params instance containing all of the computed (name, value) pairs.

    If params_map is called with debug=True, print information showing the
    flattening process.

    """
    if not kw:
        return _params_map(*args)
    else:
        def _(func):
            return _params_map(func, *args, **kw)
        return _


def only(*args):
    """Return an iter yielding args as a tuple, or ('', arg) if one arg.

    >>> list(only('a'))
    [('', 'a')]
    >>> list(only('foo', 'bar'))
    [('foo', 'bar')]

    only is useful in lambda functions wrapped by params_map when the function
    is transforming a single value rather than a generating a list.

    """
    yield ('', args[0]) if len(args) == 1 else args


@params_map
def as_value(name):
    """Map identifier strings to C(<idstring>) callspecs.

    >>> as_value('foo', 'bar')
    Params(foo=C('foo'), bar=C('bar'))

    """
    yield name, C(name)


@params_map(with_name=True)
def with_names(name, *args, **kw):
    """Add the input params_map name as the first argument of the callspec.

    >>> with_names(a='foo', b=C(2, 3))
    Params(a=C('a', 'foo'), b=C('b', 2, 3))

    """
    yield '', C(name, *args, **kw)


def for_each_name(*names):
    """Each callspec becomes a list with each name as the first arg

    >>> for_each_name('b', 'a')(x=1, y=2)
    Params(x__b=C('b', 1), x__a=C('a', 1), y__b=C('b', 2), y__a=C('a', 2))

    """
    @params_map
    def for_each_name(*args, **kw):
        for name in names:
            yield name, C(name, *args, **kw)
    return for_each_name


def add_label(label):
    """Add label as the last part of each existing name.

    >>> add_label('foo')(a=1, b=2)
    Params(a__foo=C(1), b__foo=C(2))

    This is useful when using a Params in more than one context.

    """
    @params_map
    def add_label(*args, **kw):
        yield label, C(*args, **kw)
    return add_label


def for_each_function(*functions):
    """Each callspec becomes a list with each function as the first arg and the
    function name added to the entry name.

    >>> for_each_function(int, str)(x=1)
    Params(x__int=C(<class 'int'>, 1), x__str=C(<class 'str'>, 1))

    """
    @params_map
    def for_each_function(*args, **kw):
        for function in functions:
            yield function.__name__, C(function, *args, **kw)
    return for_each_function


# We could factor a common core out of these next two, but the error
# messages when the selection function fails would be more confusing.

def include_if(include_test, *, label=''):
    """Include only what passes include_test in returned Params.

    Call include_test using the callspec as if with_namelist was specified, and
    only include the original entry in the output Params if include_test
    returns true.  If label is specified, add it to the existing label.

    >>> include_if(lambda n, *args: n.has_any('a'), label='x')(a=1, b=2)
    Params(a__x=C(1))

    """
    @params_map(with_name=True)
    def include_if(name, *args, **kw):
        if include_test(NameList(name), *args, **kw):
            yield label, C(*args, **kw)
    return include_if

def include_unless(omit_test, *, label=''):
    """Include only what passes include_test in returned Params.

    Call omit_test using the callspec as if with_namelist was specified, and
    omit the entry in the output Params if omit_test returns true.  If label is
    specified, add it to the existing label of all retained entries.

    >>> include_unless(lambda n, *args: n.has_any('a'), label='x')(a=1, b=2)
    Params(b__x=C(2))

    """
    Params(foo__a=C(1))
    @params_map(with_name=True)
    def include_unless(name, *args, **kw):
        if omit_test(NameList(name), *args, **kw):
            return
        yield label, C(*args, **kw)
    return include_unless


class NameList(list):

    """Encapsulate a test name, making the components of the accessible.

    Split the test name into a list at '__' characters, so that it is at base a
    list of the name components that were used to construct the name by one or
    more param_maps (assuming that '__' has only been used in names via
    param_maps concatenation).  The string representation of the object should
    be the original name.

    """

    def __new__(cls, name):
        return super().__new__(cls)

    def __init__(self, name):
        super().__init__(name.split('__') if name else [])

    def __str__(self):
        return '__'.join(self)

    def has_any(self, *names):
        """Return True if any name is an element of the name list

        names may be passed as a single tuple or a list of arguments.
        """
        if len(names) == 1 and not hasattr(names[0], 'encode'):
            names = names[0]
        return any(name and name in self for name in names)


    def has_all(self, *names):
        """Return True if all of the names are elements of the name list"""
        names = [n for n in names if n]
        if not names:
            return False
        return all(name in self for name in names)


def params(*args, **kw):
    """Mark decorated func so that it will be called using specified callspecs.

    If one or more Params objects, and/or any keyword arguments are supplied,
    combine everything into a single Params object.  Raise an error if there
    are any duplicate keys.  If no argument list is specified, create an empty
    Params instead.  Store the resulting Params object on the function for
    later use by ParamsMixin.

    """
    if len(args) == 1 and not kw and callable( (func:= args[0]) ):
        func._params_ = False
        return func
    def params_decorator(func):
        func._params_ = Params(*args, **kw)
        return func
    return params_decorator


class ParamsMixin:

    """
    Replace params decorated test methods with calls to it using callspecs.

    Transform each attribute in the class that has been marked by the params
    decorator by renaming it to have a "private" name (one starting with at
    least one underscore) and creating a series of new test methods that will
    call the decorated method using the callspecs that are associated with the
    decorated function.

    If the params decorator attached a Params object to the method, create the
    test names that use these call specs by joining the original method name
    with the key from the Params object using '__'.  If the class contains
    attributes whose names start with 'params_' plus the original name of the
    method, join the attribute name with 'params_' removed from the front and
    '__' added to the end as a prefix to each key in the parameter's value.

    Raise an error if a duplicate name occurs.

    """

    paramsAttributePrefix = 'params_'
    paramsDebug = False
    paramsRequired = True

    @classmethod
    def __init_subclass__(cls, *args, **kwargs):
        """Turn each test decorated with @params into a series of tests.

        """
        super().__init_subclass__(*args, **kwargs)
        params_func_attrs = {}
        params_attrs = {}
        for name, attr in cls.__dict__.items():
            if hasattr(attr, '_params_'):
                params_func_attrs[name] = attr
                if __debug__ and cls.paramsDebug:
                    print(f'@params method {name!r}')
            elif name.startswith(cls.paramsAttributePrefix):
                if __debug__ and cls.paramsDebug:
                    print(f'{cls.paramsAttributePrefix} attribute {name!r}')
                params_attrs[name] = attr
        # Associate the params_ with the function with the matching name.
        params = collections.defaultdict(list)
        for pname, paramset in params_attrs.items():
            if not isinstance(paramset, Params):
                raise ValueError(
                    f'value of params constant {pname} must be a Params'
                    f' dictionary, not {type(paramset)}'
                    )
            n = pname.removeprefix(cls.paramsAttributePrefix)
            # Loop, in case the test name has one or more '__' in it...
            tn = []
            while n:
                if n in params_func_attrs:
                    break
                if '__' not in n:
                    raise ValueError(f'No @params test found for {pname!r}')
                n, t = n.rsplit('__', 1)
                if cls.paramsDebug:
                    print(f'{n=} {t=}')
                tn.insert(0, t)
            params[n].append(('__'.join(tn), paramset))
        for fname, func in params_func_attrs.items():
            if __debug__ and cls.paramsDebug:
                print(
                    f"{fname!r} has{'' if func._params_ else ' no'} decorator"
                    f" params and {(n := len(params[fname]))}"
                    f" {cls.paramsAttributePrefix}"
                    f" attribute{'' if n == 1 else 's'}",
                    )
            all_params = func._params_
            if all_params is False:
                if not params[fname]:
                    raise ValueError(f'No params found for {fname!r}')
                all_params = Params()
            for pn, ps in params[fname]:
                try:
                    pr = pn + '__' if pn else pn
                    all_params.update(
                        **{f'{pr}{n}' if pn else n: v for n, v in ps.items()}
                        )
                except Exception as ex:
                    raise ValueError(
                        f"error combining '{cls.paramsAttributePrefix}"
                        f"{fname}{'__' if pn else ''}{pn}'"
                        f" with existing params"
                        ) from ex
            if cls.paramsRequired and not all_params:
                raise ValueError(
                    f"paramsRequired is set and {fname!r} has no params",
                    )
            impl_name = '__' + fname
            delattr(cls, fname)
            setattr(cls, impl_name, func)
            for (test_name, callspec) in all_params.items():
                test = (
                    lambda self, impl_name=impl_name, callspec=callspec:
                           callspec(getattr(self, impl_name))
                    )
                test.__name__ = fname + '__' + test_name
                setattr(cls, test.__name__, test)
                if __debug__ and cls.paramsDebug:
                    print(f'generated {callspec.repr_call(test)}')
