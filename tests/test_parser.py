# pylint: disable=anomalous-backslash-in-string, too-many-locals, too-many-statements, too-many-branches
"""
Testing for ContextFreeGrammar objects located in src/parser/parser.py
"""
import pytest
from src.parser.parser import ContextFreeGrammar


class TestParser(object):
    """
    A test suite for testing the ContextFreeGrammar object.
    """

    @staticmethod
    def _run(**kwargs):
        """
        The 'main' for testing which creates the required object and compares
        the results are what was expected, failing appropriately if they are
        not.
        """
        context_free_grammar = ContextFreeGrammar(kwargs['name'],
                                                  kwargs['productions'],
                                                  kwargs['start'])

        if context_free_grammar.name() != kwargs['name']:
            raise ValueError('Invalid name produced')

        if context_free_grammar.start() != kwargs['start']:
            raise ValueError('Invalid start production produced')

        if context_free_grammar.terminals() != kwargs['terminals']:
            raise ValueError('Invalid terminal set produced')

        if context_free_grammar.nonterminals() != kwargs['nonterminals']:
            raise ValueError('Invalid nonterminal set produced')

        first = context_free_grammar.first()
        if len(first) != len(kwargs['first']):
            raise ValueError('Invalid first set size produced')

        for elem in kwargs['first']:
            if first.get(elem, None) != kwargs['first'][elem]:
                raise ValueError('Invalid first set produced')

        follow = context_free_grammar.follow()
        if len(follow) != len(kwargs['follow']):
            raise ValueError('Invalid follow set size produced')

        for elem in kwargs['follow']:
            if follow.get(elem, None) != kwargs['follow'][elem]:
                raise ValueError('Invalid follow set produced')

        rules = context_free_grammar.rules()
        if len(rules) != len(kwargs['rules']):
            raise ValueError('Invalid number of table rules produced')

        _map = {}
        for (idx, (nonterminal, rule)) in enumerate(rules):
            found = False
            for (_idx, (_nonterminal, _rule)) in enumerate(kwargs['rules']):
                if nonterminal == _nonterminal and \
                   len(rule) == len(_rule) and \
                   all([rule[i] == e for i, e in enumerate(_rule)]):
                    _map[idx] = _idx
                    found = True
                    break

            if not found:
                raise ValueError('Invalid production rule produced')

        _cols = {t:i for i, t in enumerate(kwargs['table'].pop(0)[1:])}
        _rows = {n:i for i, n in enumerate([r.pop(0) for r in kwargs['table']])}

        table, rows, cols = context_free_grammar.table()
        print table, rows, cols
        if len(rows) != len(_rows) or set(rows.keys()) ^ set(_rows.keys()):
            raise ValueError('Invalid number of table row headers produced')

        if len(cols) != len(_cols) or set(cols.keys()) ^ set(_cols.keys()):
            raise ValueError('Invalid number of table column headers produced')

        if len(table) != len(kwargs['table']):
            raise ValueError('Invalid number of table rows produced')

        if not all([len(table[i]) == len(r) for i, r in enumerate(kwargs['table'])]):
            raise ValueError('Invalid number of table columns produced')

        fail = False
        for row in rows:
            for col in cols:
                produced = {_map[elem] for elem in table[rows[row]][cols[col]]}
                expected = kwargs['table'][_rows[row]][_cols[col]]
                if produced != expected:
                    raise ValueError('Invalid table value produced')
                if len(expected) > 1:
                    fail = True

        if fail:
            raise ValueError('conflict present in parse table')

    @staticmethod
    @pytest.mark.xfail(
        reason='First/first conflict.',
        raises=ValueError,
    )
    def test_first_first_conflict():
        """
        Valid example but produces a first/first conflict.
        """
        TestParser._run(**{
            'name': 'First/First Conflict',
            'productions': {
                '<S>': '<E> | <E> a',
                '<E>': 'b |'
            },
            'start': '<S>',
            'terminals': set(['a', 'b']),
            'nonterminals': set(['<S>', '<E>']),
            'first': {
                'a': set(['a']),
                'b': set(['b']),
                '<S>': set(['b', 'a', 1]),
                '<E>': set(['b', 1])
            },
            'follow': {
                '<S>': set([0]),
                '<E>': set([0, 'a'])
            },
            'rules': [
                ('<S>', ['<E>']),
                ('<S>', ['<E>', 'a']),
                ('<E>', ['b']),
                ('<E>', [])
            ],
            'table': [
                [' ', 'a', 0, 'b'],
                ['<S>', set([1]), set([0]), set([0, 1])],
                ['<E>', set([3]), set([3]), set([2])]
            ]
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='First/follow conflict.',
        raises=ValueError,
    )
    def test_first_follow_conflict():
        """
        Valid example but produces a first/follow conflict.
        """
        TestParser._run(**{
            'name': 'First/Follow Conflict',
            'productions': {
                '<S>': '<A> a b',
                '<A>': 'a |'
            },
            'start': '<S>',
            'terminals': set(['a', 'b']),
            'nonterminals': set(['<S>', '<A>']),
            'first': {
                'a': set(['a']),
                'b': set(['b']),
                '<S>': set(['a']),
                '<A>': set(['a', 1])
            },
            'follow': {
                '<S>': set([0]),
                '<A>': set(['a'])
            },
            'rules': [
                ('<S>', ['<A>', 'a', 'b']),
                ('<A>', ['a']),
                ('<A>', [])
            ],
            'table': [
                [' ', 'a', 0, 'b'],
                ['<S>', set([0]), set([]), set([])],
                ['<A>', set([1, 2]), set([]), set([])]
            ]
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Left recursive.',
        raises=ValueError,
    )
    def test_left_recursion():
        """
        Valid example but produces some conflicts due to the use of left
        recursion.
        """
        TestParser._run(**{
            'name': 'Left Recursion',
            'productions': {
                '<E>': '<E> <A> <T> | <T>',
                '<A>': '+ | -',
                '<T>': '<T> <M> <F> | <F>',
                '<M>': '*',
                '<F>': '( <E> ) | id'
            },
            'start': '<E>',
            'terminals': set(['(', ')', '+', '*', '-', 'id']),
            'nonterminals': set(['<E>', '<A>', '<T>', '<M>', '<F>']),
            'first': {
                '(': set(['(']),
                ')': set([')']),
                '+': set(['+']),
                '-': set(['-']),
                '*': set(['*']),
                'id': set(['id']),
                '<E>': set(['(', 'id']),
                '<A>': set(['+', '-']),
                '<T>': set(['(', 'id']),
                '<M>': set(['*']),
                '<F>': set(['(', 'id'])
            },
            'follow': {
                '<E>': set([0, '+', '-', ')']),
                '<A>': set(['(', 'id']),
                '<T>': set([0, '+', '-', '*', ')']),
                '<M>': set(['(', 'id']),
                '<F>': set([0, '+', '-', '*', ')'])
            },
            'rules': [
                ('<E>', ['<E>', '<A>', '<T>']),
                ('<E>', ['<T>']),
                ('<A>', ['+']),
                ('<A>', ['-']),
                ('<T>', ['<T>', '<M>', '<F>']),
                ('<T>', ['<F>']),
                ('<M>', ['*']),
                ('<F>', ['(', '<E>', ')']),
                ('<F>', ['id'])
            ],
            'table': [
                [' ', 0, 'id', ')', '(', '+', '*', '-'],
                ['<E>', set([]), set([0, 1]), set([]), set([0, 1]), set([]),
                 set([]), set([])],
                ['<A>', set([]), set([]), set([]), set([]), set([2]), set([]),
                 set([3])],
                ['<M>', set([]), set([]), set([]), set([]), set([]), set([6]),
                 set([])],
                ['<T>', set([]), set([4, 5]), set([]), set([4, 5]), set([]),
                 set([]), set([])],
                ['<F>', set([]), set([8]), set([]), set([7]), set([]), set([]),
                 set([])]
            ]
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Name is not of type: string',
        raises=TypeError,
    )
    def test_invalid_name():
        """
        Ensure an error is thrown when constructing a ContextFreeGrammar object
        if the name is not of type string.
        """
        TestParser._run(**{
            'name': False,
            'productions': {
                'Invalid Name Type': '<E> | <E> a'
            },
            'start': '<S>',
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Start is not of type: string',
        raises=TypeError,
    )
    def test_invalid_start_type():
        """
        Ensure an error is thrown when constructing a ContextFreeGrammar object
        if the start production is not of type string.
        """
        TestParser._run(**{
            'name': 'Invalid Start Type',
            'productions': {
                '<S>': '<E> | <E> a'
            },
            'start': False,
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Productions is not of type: dict[string, string]',
        raises=TypeError,
    )
    def test_invalid_production():
        """
        Ensure an error is thrown when constructing a ContextFreeGrammar object
        if the productions are not of type dict[string, string].
        """
        TestParser._run(**{
            'name': 'Invalid Production Rules',
            'productions': None,
            'start': False,
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Productions is not of type: dict[string, string]',
        raises=TypeError,
    )
    def test_invalid_production_nonterminal():
        """
        Ensure an error is thrown when constructing a ContextFreeGrammar object
        if the productions are not of type dict[string, string].
        """
        TestParser._run(**{
            'name': 'Invalid Production Rules',
            'productions': {
                None: '<E> | <E> a'
            },
            'start': False,
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    @pytest.mark.xfail(
        reason='Productions is not of type: dict[string, string]',
        raises=TypeError,
    )
    def test_invalid_production_rule():
        """
        Ensure an error is thrown when constructing a ContextFreeGrammar object
        if the productions are not of type dict[string, string].
        """
        TestParser._run(**{
            'name': 'Invalid Nonterminal',
            'productions': {
                '<S>': None
            },
            'start': False,
            'terminals': None,
            'nonterminals': None,
            'first': None,
            'follow': None,
            'rules': None,
            'table': None
        })

    @staticmethod
    def test_grammar_no_epsilon():
        """
        Ensure the creation of a simple grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'No Epsilon',
            'productions': {
                '<S>': '<A> a <A> b | <B> b <B> a',
                '<A>': '',
                '<B>': ''
            },
            'start': '<S>',
            'terminals': set(['a', 'b']),
            'nonterminals': set(['<S>', '<A>', '<B>']),
            'first': {
                'a': set(['a']),
                'b': set(['b']),
                '<S>': set(['a', 'b']),
                '<A>': set([1]),
                '<B>': set([1])
            },
            'follow': {
                '<S>': set([0]),
                '<A>': set(['b', 'a']),
                '<B>': set(['a', 'b'])
            },
            'rules': [
                ('<S>', ['<A>', 'a', '<A>', 'b']),
                ('<S>', ['<B>', 'b', '<B>', 'a']),
                ('<A>', []),
                ('<B>', [])
            ],
            'table': [
                [' ', 0, 'a', 'b'],
                ['<S>', set([]), set([0]), set([1])],
                ['<A>', set([]), set([2]), set([2])],
                ['<B>', set([]), set([3]), set([3])]
            ]
        })

    @staticmethod
    def test_grammar_epsilon():
        """
        Ensure the creation of a simple grammar containing an epsilon goes as
        expected.
        """
        TestParser._run(**{
            'name': 'Epsilon',
            'productions': {
                '<E>': '<T> <E\'>',
                '<E\'>': '<A> <T> <E\'> |',
                '<A>': '+ | - ',
                '<T>': '<F> <T\'>',
                '<T\'>': '<M> <F> <T\'> |',
                '<M>': '*',
                '<F>': '( <E> ) | id'
            },
            'start': '<E>',
            'terminals': set(['+', '-', '*', '(', ')', 'id']),
            'nonterminals': set(['<E>', '<E\'>', '<A>', '<T>', '<T\'>', '<M>',
                                 '<F>']),
            'first': {
                '+': set(['+']),
                '-': set(['-']),
                '*': set(['*']),
                '(': set(['(']),
                ')': set([')']),
                'id': set(['id']),
                '<E>': set(['(', 'id']),
                '<E\'>': set(['+', '-', 1]),
                '<A>': set(['+', '-']),
                '<T>': set(['(', 'id']),
                '<T\'>': set([1, '*']),
                '<M>': set(['*']),
                '<F>': set(['(', 'id'])
            },
            'follow': {
                '<E>': set([0, ')']),
                '<E\'>': set([0, ')']),
                '<A>': set(['(', 'id']),
                '<T>': set([')', '+', '-', 0]),
                '<T\'>': set([')', '+', '-', 0]),
                '<M>': set(['(', 'id']),
                '<F>': set([')', '+', '-', '*', 0])
            },
            'rules': [
                ('<E>', ['<T>', '<E\'>']),
                ('<E\'>', ['<A>', '<T>', '<E\'>']),
                ('<E\'>', []),
                ('<A>', ['+']),
                ('<A>', ['-']),
                ('<T>', ['<F>', '<T\'>']),
                ('<T\'>', ['<M>', '<F>', '<T\'>']),
                ('<T\'>', []),
                ('<M>', ['*']),
                ('<F>', ['(', '<E>', ')']),
                ('<F>', ['id'])
            ],
            'table': [
                [' ', 0, 'id', ')', '(', '+', '*', '-'],
                ['<E>', set([]), set([0]), set([]), set([0]), set([]), set([]),
                 set([])],
                ['<E\'>', set([2]), set([]), set([2]), set([]), set([1]),
                 set([]), set([1])],
                ['<A>', set([]), set([]), set([]), set([]), set([3]), set([]),
                 set([4])],
                ['<T>', set([]), set([5]), set([]), set([5]), set([]), set([]),
                 set([])],
                ['<T\'>', set([7]), set([]), set([7]), set([]), set([7]),
                 set([6]), set([7])],
                ['<M>', set([]), set([]), set([]), set([]), set([]), set([8]),
                 set([])],
                ['<F>', set([]), set([10]), set([]), set([9]), set([]),
                 set([]), set([])]
            ]
        })

    @staticmethod
    def test_grammar_simple_language():
        """
        Ensure the creation of a simple langugage grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'Simple language',
            'productions': {
                '<STMT>': 'if <EXPR> then <STMT>\
                            | while <EXPR> do <STMT>\
                            | <EXPR>',
                '<EXPR>': '<TERM> -> id\
                            | zero? <TERM>\
                            | not <EXPR>\
                            | ++ id\
                            | -- id',
                '<TERM>': 'id | constant',
                '<BLOCK>': '<STMT> | { <STMTS> }',
                '<STMTS>': '<STMT> <STMTS> |'
            },
            'start': '<STMTS>',
            'terminals': set(['if', 'then', 'while', 'do', '->', 'zero?',
                              'not', '++', '--', 'id', 'constant', '{', '}']),
            'nonterminals': set(['<STMT>', '<STMTS>', '<BLOCK>', '<TERM>',
                                 '<EXPR>']),
            'first': {
                'if': set(['if']),
                'then': set(['then']),
                'while': set(['while']),
                'do': set(['do']),
                '->': set(['->']),
                'zero?': set(['zero?']),
                'not': set(['not']),
                '++': set(['++']),
                '--': set(['--']),
                'id': set(['id']),
                'constant': set(['constant']),
                '{': set(['{']),
                '}': set(['}']),
                '<STMT>': set(['constant', '++', 'zero?', 'while', 'not', '--',
                               'id', 'if']),
                '<STMTS>': set([1, 'constant', '++', 'zero?', 'while', 'not',
                                '--', 'id', 'if']),
                '<BLOCK>': set(['constant', '++', 'zero?', 'while', 'not', '--',
                                '{', 'id', 'if']),
                '<TERM>': set(['constant', 'id']),
                '<EXPR>': set(['++', 'not', 'constant', 'zero?', '--', 'id'])
            },
            'follow': {
                '<STMT>': set([0, 'constant', '++', 'not', 'while', 'zero?',
                               '--', '}', 'id', 'if']),
                '<STMTS>': set([0, '}']),
                '<BLOCK>': set([]),
                '<TERM>': set([0, 'then', 'constant', 'do', 'not', 'id', 'if',
                               '++', '--', 'while', 'zero?', '->', '}']),
                '<EXPR>': set([0, 'then', 'constant', 'do', '++', '--',
                               'while', 'not', 'zero?', '}', 'id', 'if'])
            },
            'rules': [
                ('<STMT>', ['if', '<EXPR>', 'then', '<STMT>']),
                ('<STMT>', ['while', '<EXPR>', 'do', '<STMT>']),
                ('<STMT>', ['<EXPR>']),
                ('<EXPR>', ['<TERM>', '->', 'id']),
                ('<EXPR>', ['zero?', '<TERM>']),
                ('<EXPR>', ['not', '<EXPR>']),
                ('<EXPR>', ['++', 'id']),
                ('<EXPR>', ['--', 'id']),
                ('<TERM>', ['id']),
                ('<TERM>', ['constant']),
                ('<BLOCK>', ['<STMT>']),
                ('<BLOCK>', ['{', '<STMTS>', '}']),
                ('<STMTS>', ['<STMT>', '<STMTS>']),
                ('<STMTS>', [])
            ],
            'table': [
                [' ', 0, 'then', 'constant', 'do', '++', 'zero?', 'while',
                 'not', '--', '{', '->', '}', 'id', 'if'],
                ['<STMT>', set([]), set([]), set([2]), set([]), set([2]),
                 set([2]), set([1]), set([2]), set([2]), set([]), set([]),
                 set([]), set([2]), set([0])],
                ['<EXPR>', set([]), set([]), set([3]), set([]), set([6]),
                 set([4]), set([]), set([5]), set([7]), set([]), set([]),
                 set([]), set([3]), set([])],
                ['<BLOCK>', set([]), set([]), set([10]), set([]), set([10]),
                 set([10]), set([10]), set([10]), set([10]), set([11]),
                 set([]), set([]), set([10]), set([10])],
                ['<STMTS>', set([13]), set([]), set([12]), set([]), set([12]),
                 set([12]), set([12]), set([12]), set([12]), set([]), set([]),
                 set([13]), set([12]), set([12])],
                ['<TERM>', set([]), set([]), set([9]), set([]), set([]),
                 set([]), set([]), set([]), set([]), set([]), set([]), set([]),
                 set([8]), set([])]
            ]
        })

    @staticmethod
    def test_json():
        """
        Ensure the creation of the JSON grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'JSON',
            'productions': {
                '<VALUE>': 'string | number | bool | null | <OBJECT> | <ARRAY>',
                '<OBJECT>': '{ <OBJECT\'>',
                '<OBJECT\'>': '} | <MEMBERS> }',
                '<MEMBERS>': '<PAIR> <MEMBERS\'>',
                '<PAIR>': 'string : <VALUE>',
                '<MEMBERS\'>': ', <MEMBERS> |',
                '<ARRAY>': '[ <ARRAY\'>',
                '<ARRAY\'>': '] | <ELEMENTS> ]',
                '<ELEMENTS>': '<VALUE> <ELEMENTS\'>',
                '<ELEMENTS\'>': ', <ELEMENTS> |'
            },
            'start': '<VALUE>',
            'terminals': set(['{', '}', ',', '[', ']', ':', 'string', 'number',
                              'bool', 'null']),
            'nonterminals': set(['<VALUE>', '<OBJECT>', '<OBJECT\'>',
                                 '<MEMBERS>', '<PAIR>', '<MEMBERS\'>',
                                 '<ARRAY>', '<ARRAY\'>', '<ELEMENTS>',
                                 '<ELEMENTS\'>']),
            'first': {
                '{': set(['{']),
                '}': set(['}']),
                ',': set([',']),
                '[': set(['[']),
                ']': set([']']),
                ':': set([':']),
                'string': set(['string']),
                'number': set(['number']),
                'bool': set(['bool']),
                'null': set(['null']),
                '<VALUE>': set(['string', 'number', 'bool', 'null', '{', '[']),
                '<OBJECT>': set(['{']),
                '<OBJECT\'>': set(['}', 'string']),
                '<MEMBERS>': set(['string']),
                '<PAIR>': set(['string']),
                '<MEMBERS\'>': set([1, ',']),
                '<ARRAY>': set(['[']),
                '<ARRAY\'>': set([']', 'string', 'number', 'bool', 'null', '{',
                                  '[']),
                '<ELEMENTS>': set(['string', 'number', 'bool', 'null', '{',
                                   '[']),
                '<ELEMENTS\'>': set([1, ','])
            },
            'follow': {
                '<VALUE>': set([0, ']', '}', ',']),
                '<OBJECT>': set([0, ']', '}', ',']),
                '<OBJECT\'>': set([0, ']', '}', ',']),
                '<MEMBERS>': set(['}']),
                '<PAIR>': set(['}', ',']),
                '<MEMBERS\'>': set(['}']),
                '<ARRAY>': set([0, ']', '}', ',']),
                '<ARRAY\'>': set([0, ']', '}', ',']),
                '<ELEMENTS>': set([']']),
                '<ELEMENTS\'>': set([']'])
            },
            'rules': [
                ('<VALUE>', ['string']),
                ('<VALUE>', ['number']),
                ('<VALUE>', ['bool']),
                ('<VALUE>', ['null']),
                ('<VALUE>', ['<OBJECT>']),
                ('<VALUE>', ['<ARRAY>']),
                ('<OBJECT>', ['{', '<OBJECT\'>']),
                ('<OBJECT\'>', ['}']),
                ('<OBJECT\'>', ['<MEMBERS>', '}']),
                ('<MEMBERS>', ['<PAIR>', '<MEMBERS\'>']),
                ('<PAIR>', ['string', ':', '<VALUE>']),
                ('<MEMBERS\'>', [',', '<MEMBERS>']),
                ('<MEMBERS\'>', []),
                ('<ARRAY>', ['[', '<ARRAY\'>']),
                ('<ARRAY\'>', [']']),
                ('<ARRAY\'>', ['<ELEMENTS>', ']']),
                ('<ELEMENTS>', ['<VALUE>', '<ELEMENTS\'>']),
                ('<ELEMENTS\'>', [',', '<ELEMENTS>']),
                ('<ELEMENTS\'>', [])
            ],
            'table': [[' ', 0, ':', 'string', ']', 'number', ',', 'bool', '{',
                       'null', '}', '['],
                      ['<PAIR>', set([]), set([]), set([10]), set([]),
                       set([]), set([]), set([]), set([]), set([]),
                       set([]), set([])],
                      ['<VALUE>', set([]), set([]), set([0]), set([]),
                       set([1]), set([]), set([2]), set([4]), set([3]),
                       set([]), set([5])],
                      ['<OBJECT>', set([]), set([]), set([]), set([]),
                       set([]), set([]), set([]), set([6]), set([]),
                       set([]), set([])],
                      ['<ELEMENTS>', set([]), set([]), set([16]), set([]),
                       set([16]), set([]), set([16]), set([16]), set([16]),
                       set([]), set([16])],
                      ['<OBJECT\'>', set([]), set([]), set([8]), set([]),
                       set([]), set([]), set([]), set([]), set([]),
                       set([7]), set([])],
                      ['<MEMBERS\'>', set([]), set([]), set([]), set([]),
                       set([]), set([11]), set([]), set([]), set([]),
                       set([12]), set([])],
                      ['<ARRAY>', set([]), set([]), set([]), set([]),
                       set([]), set([]), set([]), set([]), set([]),
                       set([]), set([13])],
                      ['<MEMBERS>', set([]), set([]), set([9]), set([]),
                       set([]), set([]), set([]), set([]), set([]),
                       set([]), set([])],
                      ['<ELEMENTS\'>', set([]), set([]), set([]), set([18]),
                       set([]), set([17]), set([]), set([]), set([]),
                       set([]), set([])],
                      ["<ARRAY'>", set([]), set([]), set([15]), set([14]),
                       set([15]), set([]), set([15]), set([15]), set([15]),
                       set([]), set([15])]
                     ]
        })

    @staticmethod
    def test_ini():
        """
        Ensure the creation of the INI grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'INI',
            'productions': {
                '<INI>': '<SECTION> <INI> |',
                '<SECTION>': '<HEADER> <SETTINGS>',
                '<HEADER>': '[ string ]',
                '<SETTINGS>': '<KEY> <SEP> <VALUE> <SETTINGS> |',
                '<KEY>': 'string',
                '<SEP>': ': | =',
                '<VALUE>': 'string | number | bool'
            },
            'start': '<INI>',
            'terminals': set(['string', 'number', 'bool', ':', '=', '[', ']']),
            'nonterminals': set(['<INI>', '<SECTION>', '<HEADER>',
                                 '<SETTINGS>', '<KEY>', '<SEP>', '<VALUE>']),
            'first': {
                'string': set(['string']),
                'number': set(['number']),
                'bool': set(['bool']),
                ':': set([':']),
                '=': set(['=']),
                '[': set(['[']),
                ']': set([']']),
                '<INI>': set([1, '[']),
                '<SECTION>': set(['[']),
                '<HEADER>': set(['[']),
                '<SETTINGS>': set([1, 'string']),
                '<KEY>': set(['string']),
                '<SEP>': set([':', '=']),
                '<VALUE>': set(['string', 'number', 'bool'])
            },
            'follow': {
                '<INI>': set([0]),
                '<SECTION>': set([0, '[']),
                '<HEADER>': set([0, '[', 'string']),
                '<SETTINGS>': set([0, '[']),
                '<KEY>': set([':', '=']),
                '<SEP>': set(['string', 'number', 'bool']),
                '<VALUE>': set([0, '[', 'string'])
            },
            'rules': [
                ('<INI>', ['<SECTION>', '<INI>']),
                ('<INI>', []),
                ('<SECTION>', ['<HEADER>', '<SETTINGS>']),
                ('<HEADER>', ['[', 'string', ']']),
                ('<SETTINGS>', ['<KEY>', '<SEP>', '<VALUE>', '<SETTINGS>']),
                ('<SETTINGS>', []),
                ('<KEY>', ['string']),
                ('<SEP>', [':']),
                ('<SEP>', ['=']),
                ('<VALUE>', ['string']),
                ('<VALUE>', ['number']),
                ('<VALUE>', ['bool'])
            ],
            'table': [[' ', 0, 'bool', 'string', '=', '[', ':', ']', 'number'],
                      ['<VALUE>', set([]), set([11]), set([9]), set([]),
                       set([]), set([]), set([]), set([10])],
                      ['<KEY>', set([]), set([]), set([6]), set([]),
                       set([]), set([]), set([]), set([])],
                      ['<SETTINGS>', set([5]), set([]), set([4]), set([]),
                       set([5]), set([]), set([]), set([])],
                      ['<SECTION>', set([]), set([]), set([]), set([]),
                       set([2]), set([]), set([]), set([])],
                      ['<HEADER>', set([]), set([]), set([]), set([]),
                       set([3]), set([]), set([]), set([])],
                      ['<SEP>', set([]), set([]), set([]), set([8]),
                       set([]), set([7]), set([]), set([])],
                      ['<INI>', set([1]), set([]), set([]), set([]),
                       set([0]), set([]), set([]), set([])],
                     ]
        })

    @staticmethod
    def test_lisp():
        """
        Ensure the creation of the INI grammar goes as expected.
        """
        TestParser._run(**{
            'name': 'Lisp',
            'productions': {},
            'start': '',
            'terminals': set([]),
            'nonterminals': set([]),
            'first': {},
            'follow': {},
            'rules': [],
            'table': []
        })