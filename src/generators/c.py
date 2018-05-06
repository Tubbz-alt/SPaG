"""
A scanner/parser generator targeting c.
Generates header (.h) and source (.c) files.
"""
import datetime
from .. import generator as generator


class C(generator.Generator):
    """
    A simple object for compiling scanner's and/or parser's to c.
    """

    _reserved = {
      "auto", "break", "case", "char", "const", "continue", "default", "do",
      "int", "long", "register", "return", "short", "signed", "sizeof",
      "static", "struct", "switch", "typedef", "union", "unsigned", "void",
      "volatile", "while", "double", "else", "enum", "extern", "float", "for",
      "goto", "if"
    }

    def _sanatize(self, name):
        """
        Sanatize the name so it is safe for c compilation following the rules:
         1. Characters other than a-z, A-Z, 0-9, or _ become '_'
         2. Names beginning with a number will be prefixed with a '_'
         3. Reserved c keyword will be prefixed with a '_'
        """
        _name = ''
        for char in name:
            if char.isalnum(): _name += char
            else: _name += '_'

        if _name in self._reserved or name[0].isdigit():
            _name = '_' + _name

        return _name

    def _generate_file_header(self, filename, author, source, message, libs):
        time = datetime.datetime.utcnow().isoformat("T") + "Z"
        libs = ['#include <{0}.h>'.format(lib) for lib in libs]
        return """\
/******************************************************************************
 * File:    {0: <66}*
 * Author:  {1: <66}*
 * Created: {2: <66}*
 * Archive: {3: <66}*
 *                                                                            *
 *{4: ^76}*
 ******************************************************************************/

{6}{5}

""".format(filename, author, time, source, message,
           '\n'.join(libs), self._generate_section_header("imports"))

    def _generate_section_header(self, name):
        return """\
/******************************************************************************
 *{0: ^76}*
 ******************************************************************************/
""".format(name.upper())


    def _generate_token_api(self, name):
        types = []
        for token_name, pattern in self._scanner.expressions().items():
            types.append('  {0: <23} // {1}'.format(token_name.upper()+",", pattern))
        return """\
{2}
// Token's abstract over the character input stream.
typedef struct {0}_token {0}_token_t;

// Token's are associated to one of the types below.
typedef enum {{
{1}
}} {0}_token_type_t;

// Query for the tokens associated type.
{0}_token_type_t type({0}_token_t *{0}_token);

// Query for the string representation of the token.
const char *text({0}_token_t *{0}_token);

// Query for the file in which the token was read.
const char *source({0}_token_t *{0}_token);

// Query for the starting line on which the token was read.
unsigned long line({0}_token_t *{0}_token);

// Query for the starting column on which the token was read.
unsigned long column({0}_token_t *{0}_token);

""".format(name, "\n".join(types), self._generate_section_header("tokens")), """\
{1}
typedef struct {0}_token {{
  {0}_token_type_t type;
  const char *text;
  const char *source;
  unsigned long line;
  unsigned long column;
}} {0}_token_t;

const char *text({0}_token_t *{0}_token) {{ return {0}_token->text; }}

const char *source({0}_token_t *{0}_token) {{ return {0}_token->source; }}

unsigned long line({0}_token_t *{0}_token) {{ return {0}_token->line; }}

unsigned long column({0}_token_t *{0}_token) {{ return {0}_token->column; }}

{0}_token_type_t type({0}_token_t *{0}_token) {{ return {0}_token->type; }}

""".format(name, self._generate_section_header("tokens"))

    def _encode_dfa(self, name):
        state, symbol, T = self._scanner.transitions()

        final_states = self._scanner.accepting()

        labels, label = {}, 0
        for state_id in state.keys():
            label += 1
            labels[state_id] = "L{0}".format(label)

        program = ""
        for in_state, state_key in state.items():
            cases = ""
            for char, sym_key in symbol.items():
                _char = ord(char)
                if _char < 0 or _char > 255:
                    raise ValueError("Invalid Input: encountered non ascii character\n")
                _char = hex(_char)
                end_state = T[sym_key][state_key]
                if end_state in final_states:
                    cases += """\
    case {0}:
      return 0; // FINAL STATE
""".format(_char)
                else:
                    cases += """\
    case {0}:
      goto {1};
""".format(_char, labels[end_state])
                # FIXME:
                # - longest match
                # - build token when done
            program += """\
{0}:
  switch(({1}_scanner->peek = fgetc({1}_scanner->input))) {{
{2}   default:
      return 1;
  }}

""".format(labels[in_state], name, cases)

        return program

    def _generate_scanner_api(self, name):
        return """\
{1}
// Abstract over the reading of {0}_token_t's.
typedef struct {0}_scanner {0}_scanner_t;

// Attempt the creation of a new scanner given a file.
{0}_scanner_t *new_{0}_scanner(FILE *f);

// Free the scanner. Note: file closing is not handled.
void free_{0}_scanner({0}_scanner_t *{0}_scanner);

// Return most recently read token of the given scanner.
{0}_token_t *{0}_token({0}_scanner_t *{0}_scanner);

// Attempt to scan a token from the file. 1 if successful, otherwise 0.
// If failure occurs the token will still contain the relevant details of the
// unrecognized token except for its type.
int {0}_scan({0}_scanner_t *{0}_scanner);
""".format(name, self._generate_section_header("scanner")), """\
{2}
typedef struct {0}_scanner {{
  FILE *input;
  char peek;
  long offset;
  {0}_token_t *token;
}} {0}_scanner_t;

{0}_scanner_t *new_{0}_scanner(FILE *f) {{
  if(!f) {{ return NULL; }}

  {0}_scanner_t *{0}_scanner = malloc(sizeof({0}_scanner_t));
  if(!{0}_scanner) {{ return NULL; }}

  {0}_scanner->input = f;
  {0}_scanner->peek = fgetc(f);
  {0}_scanner->token = malloc(sizeof({0}_token_t));

  if(!{0}_scanner->token) {{
      free({0}_scanner);
      return NULL;
  }}

  return {0}_scanner;
}}

void free_{0}_scanner({0}_scanner_t *{0}_scanner) {{
  free({0}_scanner);
}}

{0}_token_t *{0}_token({0}_scanner_t *{0}_scanner) {{
  return {0}_scanner->token;
}}

int {0}_scan({0}_scanner_t *{0}_scanner) {{
  {0}_scanner->offset = ftell({0}_scanner->input);

{1}}}
""".format(name, self._encode_dfa(name), self._generate_section_header("scanner"))

    def _generate_ast_api(self, name):
        # TODO: define AST prototypes and defs
        ast_header, ast_source = "", ""
        return ast_header, ast_source

    def _encode_bnf(self, name):
        # TODO: graph encoded as GOTOs;
        # automatically throw away tokens not in the bnf (whitespace, comments, etc)
        return ""
        #production_rules = ""
        #for nonterm, rule in self._parser.rules():
        #    production_rules += "// {0: <30} ::= {1}\n".format(nonterm, " ".join(rule))
        # """\
        # // Start production ::= {2}
        #
        # {3}
        #
        # // Attempt to parse into an AST of tokens. 1 if successful, otherwise 0.
        # int {0}(FILE *f);
        # """.format(parse_func, self._generate_section_header("::BNF GRAMMMAR::"),
        #            self._parser.start(), production_rules)

    def _generate_parser_api(self, name):
        # TODO: define parser prototypes and defs
        parser_header, parser_source = "", """\
        {2}
        """.format(name, self._encode_bnf(name), self._generate_section_header("parser"))
        return parser_header, parser_source

    def output(self, filename):
        """
        Attempt to generate and write the c source(.c) and header(.h) files for
        the corresponding scanner and/or parser currently set in the object.
        """
        if type(filename) != str:
            raise ValueError('Invalid Input: filename must be a string')

        if filename == "":
            raise ValueError('Invalid Input: filename must be non empty')

        author = '**AUTO GENERATED**'
        source = 'https://github.com/rrozansk/Scanner-Parser-Generator'
        warning = 'WARNING!! AUTO GENERATED FILE, DO NOT EDIT!'
        libs = ["stdio"]

        header = self._generate_file_header(filename+".h",
                                            author,
                                            source,
                                            warning,
                                            libs)

        libs.extend(["stdlib", filename])
        source = self._generate_file_header(filename+".c",
                                            author,
                                            source,
                                            warning,
                                            libs)

        if self._scanner is not None:
            scan_func = self._sanatize(self._scanner.name())
            token_header, token_source = self._generate_token_api(scan_func)
            scanner_header, scanner_source = self._generate_scanner_api(scan_func)

            header += token_header + scanner_header
            source += token_source + scanner_source

        if self._parser is not None:
            parse_func = self._sanatize(self._parser.name())
            ast_header, ast_source = self._generate_ast_api(parse_func)
            parser_header, parser_source = self._generate_parser_api(parse_func)

            header += ast_header + parser_header
            source += ast_source + parser_source

        header = """\
#ifndef {0}
#define {0}

{1}
#endif
""".format(filename, header)

        with open(filename+".h", 'w') as _file: _file.write(header)
        with open(filename+".c", 'w') as _file: _file.write(source)
