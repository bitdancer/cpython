:mod:`!unittest.params` --- parameterizing unit tests
=====================================================

.. module:: unittest.params
   :synopsis: Parameterization support for Unittest

.. currentmodule:: unittest.params

.. versionadded:: 3.16

**Source code:** :source:`Lib/unittest/params.py`

--------------

:mod:`!unittest.params` enhances the :mod:`unittest` framework by providing a
flexible and intuitive way specify that a test method can accept parameters,
and to supply those parameters to the test method.  The heart of the module is
a :class:`unittest.TestCase` mix-in (:class:`ParamsMixin`) that adds the
mechanism for conveying parameters to parameterized test methods, a "call
specification" object (:class:`C`, also called a "callspec") that provides an
intuitive way to specify the parameter values, and a decorator (:func:`params`)
that marks test methods that are to be parameterized.

:class:`C` objects are used to specify concrete parameters values.  They can be
associated with a specific test either by specifying them in the :func:`params`
decorator arguments, or by listing them in the constructor of a specialized
dictionary (:class:`Params`) used as the value of appropriately named class
variables (:attr:`params_XXX` attributes).  Both the :func:`params` decorator
and the :class:`Params` constructor take keyword arguments, and the keyword
name becomes a label for that specific callspec.  A parameterized test method
is replaced by a series of test methods whose names are derived by combining
the test method name and the callspec label.  The resulting test name can be
used to run the test method with that specific set of concrete parameters using
the normal :mod:`unittest` test selection mechanisms (see
:ref:`unittest-command-line-interface`).


.. _unittest-params-quickguide:

Quick Guide
-----------

.. testsetup::

    import sys
    import unicodedata
    from pprint import pprint
    from subprocess import run, PIPE, STDOUT
    from unittest import TestCase
    from unittest.params import (add_label, as_value, C, for_each_function,
        include_if, include_unless, NameList, Params, params_map, ParamsMixin,
        only, with_names, for_each_name)
    def r(cmd):
        p = run(cmd, text=True, stdout=PIPE, stderr=STDOUT)
        print(p.stdout.rstrip())
    charname = lambda c: unicodedata.name(c).lower().replace(' ', '_')

Here is an example of the simplest way to use :mod:`!unittest.params`,
reprising part of the example from the main :mod:`unittest` chapter:

.. literalinclude:: ../includes/unittest-params-example1.py

.. testcode::
   :hide:

   r([sys.executable, './includes/unittest-params-example1.py', '-v'])

When run using the ``-v`` command line flag, this will produce the following
output:

.. testoutput::

    test_upper__mixed_case (...TestStringMethods.test_upper__mixed_case) ... ok
    test_upper__multiple_words (...TestStringMethods.test_upper__multiple_words) ... ok
    test_upper__one_lc_letter (...TestStringMethods.test_upper__one_lc_letter) ... ok
    test_upper__one_lc_word (...TestStringMethods.test_upper__one_lc_word) ... ok
    test_upper__one_uc_letter (...TestStringMethods.test_upper__one_uc_letter) ... ok
    test_upper__one_uc_word (...TestStringMethods.test_upper__one_uc_word) ... ok

    ----------------------------------------------------------------------
    Ran 6 tests in ...

    OK

Each callspec is tested in a separate run of the test method.  The usual
:mod:`!unittest` facilities for selecting specific tests to run will work with
these tests.  In particular you can cut and paste the test name into a
:mod:`!unittest` command just as with any other test name in the
:mod:`!unittest` output.

For small parameter sets, listing them in the decorator arguments provides
nicely compact code.  For larger lists of callspecs, using class attributes can
lead to more readable code.  If an attribute starts with the string ``params_``
followed by the name of the test, its value will be used to generate specific
tests.  The value of the attribute must be a :class:`Params` dictionary.

A ``params_`` attribute that has two underscores (``__``) after the test name,
followed by other characters, it will be recognized as specifying parameters
for the test, with the additional characters included in the generated test
name.  This provides a way to logically group callspecs:

.. literalinclude:: ../includes/unittest-params-example2.py

.. testcode::
   :hide:

   r([sys.executable, './includes/unittest-params-example2.py', '-v'])

Running this gives us:

.. testoutput::

    test_split__bad_split_char (...TestStringMethods.test_split__bad_split_char) ... ok
    test_split__on__ampersand (...TestStringMethods.test_split__on__ampersand) ... ok
    test_split__on__digit_seven (...TestStringMethods.test_split__on__digit_seven) ... ok
    test_split__on__latin_small_letter_z (...TestStringMethods.test_split__on__latin_small_letter_z) ... ok
    test_split__on__plus_sign (...TestStringMethods.test_split__on__plus_sign) ... ok
    test_split__one_word (...TestStringMethods.test_split__one_word) ... ok
    test_split__two_words (...TestStringMethods.test_split__two_words) ... ok

    ----------------------------------------------------------------------
    Ran 7 tests in ...

    OK

:mod:`!params` provides additional functions and decorators for working with
parameter sets, which are covered in the :ref:`unittest-params-reference`.

The test suite for the :mod:`params` module contains realistic examples of
almost all of the features of the module:
:source:`Lib/test/test_unittest/test_params.py`.


Parameter Sets and Parameter Maps
---------------------------------

"Params" as a module name is a shorthand for "parameters" and "parameter
values".  The module supports adding parameters to test functions, and it
supports specifying concrete parameter values (bindings of particular argument
values to particular parameters) via :class:`C` instances.  These :class:`C`
instances are gathered into "parameter sets" (technically "parameter value
sets", but that gets to be a mouthful) held in :class:`Params` dictionaries
that map names to :class:`C` instances.  These names are then used as part of
the name of the :mod:`unittest` test that runs the parameterized test method
using that particular callspec.

The :mod:`!params` module operates on parameter sets.  In the simplest usage
you declare a parameter set by writing out the mapping of names to callspecs
using keyword arguments in the :class:`Params` constructor, as shown in the
examples in the :ref:`unittest-params-quickguide`.

:mod:`!params` provides a function/decorator, :func:`params_map`, that
facilitates generating parameter sets from data, or expanding a parameter set
to run the same base set of parameters with various automatically generated
changes, or to re-use a parameter set with a different test, or to
do...anything you can implement by mapping a function onto a set of data items
or :class:`C` instances.  :func:`params_map` is essentially a :term:`flatmap`
specialized for operating on parameter sets.

:mod:`!params` also provides a number of predefined :func:`params_map` utility
functions that preform commonly needed operations on parameter sets, such as
filtering them for inclusion (:func:`include_if`) and exclusion
(:func:`include_unless`), including the name as a parameter
(:func:`with_names`), or turning a list of strings into parameters
(:func:`as_value`).  See the :ref:`unittest-params-reference` for a complete
list.

.. _unittest-params-reference:

Reference
---------


.. class:: ParamsMixin

   A mix-in class to add test method parameterization support to the
   standard :class:`unittest.TestCase`.  For example:

    .. testcode::

      class MyTestClass(ParamsMixin, TestCase):
          pass

   The mix-in should come before :class:`!TestCase` in the base class list.

   Methods decorated with the :func:`params` decorator must have at least one
   callspec defined (but see :attr:`paramsRequired`).

   Each attribute in the class that has been marked by the :func:`params`
   decorator is transformed by renaming it to have a "private" name (one
   starting with at least one underscore) and creating a series of new test
   methods that will call the decorated method using the callspecs that are
   associated with the decorated function.

   If the :func:`params` decorator has arguments, tests are created that use
   these callspecs, with names formed by using ``__`` to join the original
   method name with the key from the Params object.  If the class contains
   attributes whose names start with ``params_`` plus the original name of the
   method, tests are created whose names are formed by using ``__`` to join the
   attribute name, stripped of the ``params_`` prefix, to each key in the
   parameter's value.

   If any duplicate names occur, a :exc:`ValueError` is raised.


   .. attribute:: paramsAttributePrefix

      String giving the prefix of attribute names whose values must be
      :class:`Params` instances and which will be interpreted as dictionaries
      of callspecs for an associated test method.  The default value is
      ``params_``.

      If a class attribute name starts with :attr:`paramsAttributePrefix`, the
      remainder of the attribute name must start with a string that matches the
      name of a method of the class that is marked by the :func:`params`
      decorator.  A :exc:`ValueError` is raised at class creation time if no
      such method can be found.  The value of the attribute is used at class
      creation time to replace the test method with a series of tests calling
      the original test method.  The name for each new test is derived by using
      ``__`` to join the attribute name (with the :attr:`paramsAttributePrefix`
      removed) to the dictionary entry name.  The action of the newly created
      test method is to use the :class:`C` instance to call the original test
      method.

      More than one attribute may match the same test method, if the extended
      portion of the name starts with a ``__`` (see the second example in the
      :ref:`unittest-params-quickguide`). The decorator of the test method may
      also provide a parameter set.  A :exc:`ValueError` will be raised at
      class creation time if there are any duplicate test names in the combined
      parameter sets.

   .. attribute:: paramsRequired

      Default value: ``True``.  When ``True``, a :exc:`ValueError` is raised at
      class creation time if the combined parameter sets for a method is the
      empty set.  If ``False``, an empty combined set is not an error.  If a
      test's :func:`params` decorator does not have even an empty parameter
      list and there are no `params_` attributes for that test method, that
      raises an error even if :attr:`!paramsRequired` is ``False``.

   .. attribute:: paramsDebug

      Default value: ``False``.  If set to ``True``, debug output reporting the
      process of finding test methods and ``params_`` attributes, and of
      creating the test methods derived from the resulting parameter set, will
      be printed to stdout.


.. decorator:: params(*args, **kwargs)

   :func:`params` is a decorator for :mod:`unittest` test methods.  Positional
   arguments must be :class:`Params` instances. Callspecs (:class:`C`
   instances) may be provided via keyword arguments (see the first example in
   the :ref:`unittest-params-quickguide`).  The arguments and the keywords are
   merged, and if there are any duplicate keys a :attr:`ValueError` is raised.

   The argument list may be omitted, in which case there must be at least one
   class attribute starting with :attr:`!paramsAttributePrefix` and the test
   name, otherwise a :exc:`ValueError` is raised.



.. function:: fmt(obj, subs)

   If *obj* has a ``format`` attribute, call call a safe formatter on it,
   passing in *subs* as the dictionary of available values.  "safe formatting"
   means if a referenced variable does not exist, the format specification is
   left as is in the string, rather than raising an error.  If *obj* has an
   ``items`` attribute, call its type with an argument list consisting of a
   mapping from the keys to the values returned by calling ``items``, after
   applying the safe formatter to any values that have a ``format`` attribute,
   and return the resulting object.  If the *obj* is iterable, call its type
   with an argument consisting of a list of the results of iterating *obj*,
   after applying the safe formatter to any values that have a ``format``
   attribute, and return the resulting object.


.. function:: fmtall(obj, subs)

   Apply :func:`fmt` to *obj* recursively, using *subs*.  That is, instead of
   checking for a 'format' attribute on the dictionary or iterable values, call
   :func:`fmt` on each such value, rebuilding the object using the returned
   values.

   :func:`fmtall` does a poor man's deep copy: it does not use the deepcopy
   protocol and so does not handle data structures with cycles.  It is intended
   for use on relatively straightforward test input data.


.. class:: C(*args, **kwargs)

   Instances of :class:`!C` are referred to as a "call specifications" or
   "callspecs", and encapsulate a concrete set of parameter values.  An
   instance can be used to call another function with those values as its
   arguments.

   .. attribute:: args

      A tuple of the positional arguments passed to the constructor.

   .. attribute:: kw

      A dictionary of the keyword arguments passed to the constructor.

   As with any python object, be careful to not modify any mutable objects that
   the :attr:`args` or :attr:`kw` attributes reference.  Doing so will affect
   all code that uses the callspec, as well as any other code with references
   to those same objects.

   .. method:: __call__(func)

      Call *func*, passing :attr:`args` as positional arguments to the call,
      and :attr:`kw` as keyword arguments.  Return the result of the call.

      .. doctest::

         >>> def foo(a, b=None):
         ...     return a, b
         >>> cs1 = C(1, 2)
         >>> cs2 = C(0)
         >>> cs3 = C(4, b=0)
         >>> (cs1(foo), cs2(foo), cs3(foo))
         ((1, 2), (0, None), (4, 0))

   .. method:: __eq__(self, other)

      :class:`C` instances compare as equal if their ``args`` and ``kw``
      attributes both compare as equal.

   .. method:: repr_call(self, func)

      Returns a representation of the call that would be made if the instance
      were called on *func*:

      .. doctest::

         >>> def foo(a, b=None): pass
         >>> cs1 = C(1, 2)
         >>> cs2 = C(1, b=3)
         >>> cs1.repr_call(foo), cs2.repr_call(foo)
         ('foo(1, 2)', 'foo(1, b=3)')

   .. method:: fmt(self, **kwargs)

      Apply the :func:`~unittest.params.fmt` function to both the ``args``
      and ``kw`` attributes, using *kw* as the *subs* dictionary.

      .. doctest::

         >>> cs = C('add a {c}', x='here {c} too', y=['not {c} here'])
         >>> cs.fmt(c='z')
         C('add a z', x='here z too', y=['not {c} here'])

   .. method:: fmtall(self, **kwargs)


      Apply the :func:`~unittest.params.fmtall` function to both the ``args``
      and ``kw`` attributes, using *kw* as the *subs* dictionary.

      .. doctest::

         >>> cs = C('add a {c}', x='here {c} too', y=['and {c} here'])
         >>> cs.fmtall(c='z')
         C('add a z', x='here z too', y=['and z here'])


.. class:: Params(*args, **kwargs)

    :class:`!params` is a dictionary subclass with specialized behavior.
    All positional arguments must be :class:`Params` instances.  Keyword
    arguments may take any value; any non-:class:`C` value will become a
    single argument :class:`C` instance:

    .. doctest::

       >>> Params(a=[1, 2, 3])
       Params(a=C([1, 2, 3]))

    Once a key has been set, it cannot be replaced without first explicitly
    deleting it:

    .. doctest::

       >>> p = Params(a=1, b=2)
       >>> p['b'] = 3
       Traceback (most recent call last):
           ...
       ValueError: cannot add b=3, a callspec with that name already exists
       >>> del p['b']
       >>> p['b'] = 3
       >>> p
       Params(a=C(1), b=C(3))


.. class:: NameList(name)

   A :class:`NameList` instance is a wrapper around the result of calling
   ``split('__')`` on *name*.  In the context of the names of entries
   in a parameter set, this generally decomposes the name into a list
   of individual labels.

   For example, if we take one of the names generated by the example for
   :func:`add_label` and create a :class:`NameList` instance from it, we get
   back a list of the original component labels:

   .. doctest::

      >>> NameList('format__from_str_tests')
      ['format', 'from_str_tests']

   .. method:: __str__()

      The string representation of a :class:`NameList` is the orginal *name*:

      .. doctest::

         >>> str(NameList('format__from_str_tests'))
         'format__from_str_tests'

   .. method:: has_any(iterable)
               has_any(label[, label[...])

      Returns ``True`` if any element of *iterable* or any *label* is in the
      list of labels:

      .. doctest::

         >>> NameList('several__example__labels').has_any('several', 'labels')
         True
         >>> NameList('several__example__labels').has_any('notone')
         False
         >>> NameList('several__example__labels').has_any('notone', 'labels')
         True

   .. method:: has_all(label[, label[...])

      Returns ``True`` if all of the *label* arguments are in the list
      of labels:

      .. doctest::

         >>> NameList('several__example__labels').has_all('several', 'labels')
         True
         >>> NameList('several__example__labels').has_all('notone', 'labels')
         False


.. decorator:: params_map(with_name=False, with_Namelist=False, debug=False)

   :func:`!params_map` is a :term:`flatmap` specialized for manipulating
   parameter sets.  It is useful in both decorator form and functional form
   (using a ``lambda`` as the mapping function).  The function it returns takes
   any number of arguments and keywords, and returns a :class:`Params`
   instance.  If an argument is a :class:`Params` instance, the mapping
   function is called on each value in the instance.  Otherwise the mapping
   function is called on the argument.  The mapping function is also called on
   the value of all keyword arguments.  :class:`Params` values and keyword
   values have an existing name, all other arguments have no existing name.
   The mapping function must return an iterable of ``(label, value)`` tuples.
   If ``value`` is not a :class:`C` instance it will be turned into a single
   argument :class:`C` instance.  If ``label`` is not the empty string, ``__``
   will be used to join the existing name and the returned label.  If there is
   no existing name, ``label`` is used as the name.  If there is no existing
   name the mapping function *must* supply a label, and it must be unique among
   all such labels it returns.  If a mapping function returns more than one
   tuple, it must supply unique labels in each tuple.  In general that means
   labels must be uniquely derived from the data in some fashion.

   The mapping function is called via the :class:`C` instance that either is
   the value, or is constructed as a single argument :class:`C` from the value.
   If *with_name* or *with_namelist* is ``True``, the existing name, or the
   empty string if there isn't one, is inserted in position 0.  It is inserted
   as a string for *with_name* or wrapped in a :class:`NameList` for
   *with_namelist*.  A :attr:`ValueError` is raised if both *with_name* and
   *with_namelist* are true.

   As an example, we can enhance our split tests from the second example in the
   :ref:`unittest-params-quickguide` using the decorator form to generate
   multiple named parameters from data:

   .. testcode::

      @params_map
      def for_each_character(c):
          cn = charname(c)
          yield f'one_split__{cn}', C(f'split {c}able', c, expected=['split ', 'able'])
          yield f'no_split__{cn}', C('not splitable', c, expected=['not splitable'])
          yield f'two_split__{cn}', C(f'spl{c}i{c}t', c, expected=['spl', 'i', 't'])

      params_test_split__on = for_each_character(*list('z&+7'))

   .. testcode::
      :hide:

      print(']),\n       '.join(repr(params_test_split__on).split(']), ')))

   The resulting :class:`Params` instance looks like this:

   .. testoutput::

      Params(one_split__latin_small_letter_z=C('split zable', 'z', expected=['split ', 'able']),
             no_split__latin_small_letter_z=C('not splitable', 'z', expected=['not splitable']),
             two_split__latin_small_letter_z=C('splzizt', 'z', expected=['spl', 'i', 't']),
             one_split__ampersand=C('split &able', '&', expected=['split ', 'able']),
             no_split__ampersand=C('not splitable', '&', expected=['not splitable']),
             two_split__ampersand=C('spl&i&t', '&', expected=['spl', 'i', 't']),
             one_split__plus_sign=C('split +able', '+', expected=['split ', 'able']),
             no_split__plus_sign=C('not splitable', '+', expected=['not splitable']),
             two_split__plus_sign=C('spl+i+t', '+', expected=['spl', 'i', 't']),
             one_split__digit_seven=C('split 7able', '7', expected=['split ', 'able']),
             no_split__digit_seven=C('not splitable', '7', expected=['not splitable']),
             two_split__digit_seven=C('spl7i7t', '7', expected=['spl', 'i', 't']))


   :func:`params_map` can also be called using the function call pattern,
   typically using a ``lambda`` as a mapping function.  We can simplify the
   first example in the :ref:`unittest-params-quickguide` by using a ``lambda``
   based map:

   .. testcode::

      params_test_upper = Params(
          params_map(with_name=True)(lambda n, v: [('', C(n, v))])(
              a='A', A='A', word='WORD', WORD='WORD', MiXEd='MIXED'),
          multiple_words = C(
              'test EvErYthing AT ONCE',
              'TEST EVERYTHING AT ONCE',
              ),
          )

   .. testcode::
      :hide:

      print('),\n       '.join(repr(params_test_upper).split('), ')))

   The test names produced this way are perhaps not optimal in this case, but
   it does demonstrate the principle:

   .. testoutput::

      Params(a=C('a', 'A'),
             A=C('A', 'A'),
             word=C('word', 'WORD'),
             WORD=C('WORD', 'WORD'),
             MiXEd=C('MiXEd', 'MIXED'),
             multiple_words=C('test EvErYthing AT ONCE', 'TEST EVERYTHING AT ONCE'))


.. function:: only([label], value)

   :func:`only` is intended for use in :meth:`params_map` functional calls.
   Frequenty map functions used in this way only return one tuple, and that
   usually does not add a label.  Given a single value, :func:`only` returns a
   list consisting of a single tuple with an empty label.  If given
   two values, it returns a list containing of a tuple of those two values.
   Thus it produces "only" one value when used in a :func:`params_map`
   ``lambda`` function.

   Using :func:`only`, the :func:`params_map` ``lambda`` call example above
   becomes:

   .. testcode::

      result = params_map(with_name=True)(lambda n, v: only(C(n, v)))(
          a='A', A='A', word='WORD', WORD='WORD', MiXEd='MIXED')

   .. testcode::
      :hide:

      print('),\n       '.join(repr(result).split('), ')))

   .. testoutput::
      :hide:

      Params(a=C('a', 'A'),
             A=C('A', 'A'),
             word=C('word', 'WORD'),
             WORD=C('WORD', 'WORD'),
             MiXEd=C('MiXEd', 'MIXED'))

.. function:: as_value(*labels)

   :func:`as_value` turns a list of (identifier) strings into single argument
   :class:`C`\ s, using the string as both the label and the argument.  This
   comes in handy in situations where that single string can trigger the
   desired variation in the test.

   For example, there are several string methods that will return the string
   unchanged when called on an alphabetic string.  We can write a test that
   asserts this idempotence:

   .. testcode::

       def test_noop(self, method):
           self.assertEqual('foo', getattr('foo', method)())

   And then generate tests for each method that should pass it:

   .. testcode::

       params_test_noop = as_value('format', 'strip', 'expandtabs')

   .. testcode::
      :hide:

      print(params_test_noop)

   .. testoutput::

      Params(format=C('format'), strip=C('strip'), expandtabs=C('expandtabs'))


.. function:: with_names(*args, **kwargs)

   :func:`with_names` takes :mod:`Params` instances as arguments, and/or
   keyword values.  It adds the existing name as the first argument of the
   callspecs it creates in the :mod:`Params` instance it returns.

   For example, we could test the error messages returned when calling various
   string methods with no arguments:

   .. testcode::

      def test_missing_arguments(self, method, expected_msg):
          with self.assertRaisesRegex(TypeError, expected_msg):
              getattr('teststring', method)()

      params_test_missing_arguments = with_names(
          join = 'takes exactly one',
          index = 'takes at least one',
          maketrans = 'expected at least 1',
          )

   .. testcode::
      :hide:

      print('),\n       '.join(repr(params_test_missing_arguments).split('), ')))

   .. testoutput::

      Params(join=C('join', 'takes exactly one'),
             index=C('index', 'takes at least one'),
             maketrans=C('maketrans', 'expected at least 1'))



.. function:: add_label(label)(*args, **kwargs)

   :func:`add_label` is a :func:`params_map` constructor.  It returns a
   :func:`params_map` that adds a fixed label to each existing callspec.
   This is primarily useful when reusing a parameter set, allowing the
   generated test name to indicate where the callspec came from.

   For example, suppose we have a class, ``mystr``, that we want to ensure
   mimics the ``str`` API:

   .. testcode::

      def test_mystr_noop_if_no_args(self,  method):
          s = mystr('abc')
          self.assertEqual(s, getattr(s, method)())

      params_test_mystr_noop = add_label('from_str_tests')(
          params_test_noop)

   .. testcode::
      :hide:

      print('),\n       '.join(repr(params_test_mystr_noop).split('), ')))

   .. testoutput::

      Params(format__from_str_tests=C('format'),
             strip__from_str_tests=C('strip'),
             expandtabs__from_str_tests=C('expandtabs'))


.. function:: for_each_name(*names)(*args, **kwargs)

   :func:`for_each_name` is a :func:`params_map` constructor.  It returns a
   :func:`params_map` that generates new callspecs for each input callspec,
   adding each *name* as the first argument of the new callspecs, and using
   *name* as an additional label.

   For example, we can expand the example from :func:`as_value` to test more
   than one base string:

   .. testcode::

      def test_noop_2(self, s, method):
          self.assertEqual(s, getattr(s, method)())

      params_test_noop_2 = for_each_name("foo", "123")(
          as_value('format', 'strip', 'expandtabs')
          )

   .. testcode::
      :hide:

      print('),\n       '.join(repr(params_test_noop_2).split('), ')))

   .. testoutput::

          Params(format__foo=C('foo', 'format'),
                 format__123=C('123', 'format'),
                 strip__foo=C('foo', 'strip'),
                 strip__123=C('123', 'strip'),
                 expandtabs__foo=C('foo', 'expandtabs'),
                 expandtabs__123=C('123', 'expandtabs'))

  The end result of joining the *name* string to the existing name must be a
  valid identifier, otherwise a :exc:`ValueError` will be raised.


.. function:: for_each_function(*functions)(*args, **kwargs)

   :func:`for_each_function` is a :func:`params_map` constructor.  It returns a
   :func:`params_map` that generates new callspecs for each input callspec,
   adding each *function* as the first argument of the new callspecs, and
   adding the __name__ of the function as an additional label.

   For example, we could use it to expand the argument-count-error tests:

   .. testcode::

      def test_missing_arguments(self, method, expected_msg):
          with self.assertRaisesRegex(TypeError, expected_msg):
              method()

      params_test_missing_arguments = Params(
          for_each_function( ''.startswith, ''.endswith, ''.count)(
              'takes at least 1'),
          for_each_function( ''.format_map, ''.join)(
              'takes exactly 1'),
          )

   .. testcode::
      :hide:

      print('),\n       '.join(repr(params_test_missing_arguments).split('), ')))

   .. testoutput::

      Params(startswith=C(<built-in method startswith...>, 'takes at least 1'),
             endswith=C(<built-in method endswith...>, 'takes at least 1'),
             count=C(<built-in method count ...>, 'takes at least 1'),
             format_map=C(<built-in method format_map ...>, 'takes exactly 1'),
             join=C(<built-in method join of str ...>, 'takes exactly 1'))


.. function:: include_unless(func, label='')(*args, **kwargs)

   :func:`include_unless` is a :func:`params_map` constructor.  It returns a
   :func:`params_map` that filters a parameter set, including everything
   except those callspecs for which *func* returns ``True``.  *label* is
   returned as an additional label for the callspec, if specified.

   *func* is called using the existing callspec, but adding an additional
   arugment to the front, a :class:`NameList` instance for the existing
   callspec name.

   For example, suppose we have a custom string class that mimics the ``str``
   API, but its ``split`` method does something special with the ``&``
   character.  So all of the ``params_test_split__on`` callspecs generated
   in the :func:`params_map` exmaple would apply, except for the three
   involving the ampersand:

   .. testcode::

      params_test_mystr_split__on = include_unless(
          lambda n, *a, **k: 'ampersand' in n)(params_test_split__on)
      print(len(params_test_split__on), len(params_test_mystr_split__on))

   .. testoutput::

      12 9


.. function:: include_if(func, label='')(*args, **kwargs)

   :func:`include_if` is a :func:`params_map` constructor.  It returns a
   :func:`params_map` that filters a parameter set, including only
   callspecs for which *func* returns ``True``.  *label* is returned as
   an additional label for the callspec, if specified.

   *func* is called using the existing callspec, but adding an additional
   arugment to the front, a :class:`NameList` instance for the existing
   callspec name.

   For example, suppose our mystr split function does something special
   for *all* non-alphanumeric characters:

   .. testcode::

      params_test_mystr_split__on = include_if(
          lambda n, s, c, **k: c.isalnum())(params_test_split__on)
      print(len(params_test_split__on), len(params_test_mystr_split__on))

   .. testoutput::

      12 6
