# -*- coding:utf-8 -*-

import sys
import argparse
import re
import locale
import ast
import codecs
import fileinput
import os
import six
import io
import shutil
import re
import collections
import subprocess

SHORTAPPNAME = "tse"
LOGAPPNAME = "Text Stream Editor in Python"
SCRIPTFILE = os.path.join(os.path.expanduser(u"~"), ".tserc")


class Env:
    actions = ()
    begincode = None
    endcode = None
    inputenc = outputenc = sys.getfilesystemencoding()
    inputerrors = outputerrors = 'strict'
    encoding = locale.getpreferredencoding()
    scriptfile = SCRIPTFILE

    def __init__(self, statement, begin, end, input_encoding, output_encoding,
                 module, module_star, script_file, inplace, ignore_case, field_separator, files):
        self.ignore_case = ignore_case
        self.field_separator = field_separator

        if statement:
            self.actions = [(self.build_re(r), self.build_code(c))
                            for (r, c) in self._parse_statement(statement)]

        if begin:
            self.begincode = self.build_code(s for b in begin for s in b)
        if end:
            self.endcode = self.build_code(s for e in end for s in e)

        if input_encoding:
            enc, _, errors = (s.strip() for s in input_encoding.partition(':'))
            if enc:
                self.inputenc = enc
            if errors:
                self.inputerrors = errors

        if output_encoding:
            enc, _, errors = (s.strip()
                              for s in output_encoding.partition(':'))
            if enc:
                self.outputenc = enc
            if errors:
                self.outputerrors = errors

        if script_file:
            self.scriptfile = script_file
        self.inplace = inplace
        self.imports = module or ()
        self.imports_str = module_star or ()
        self.files = files or ()

    def _parse_statement(self, statement):
        pattern = None
        actions = []
        for argtype, values in statement:
            if argtype == StatementAction.ARGTYPE:
                if pattern is not None:
                    yield pattern, actions
                    pattern = None
                    actions = []
                yield values[0], values[1:]

            elif argtype == PatternAction.ARGTYPE:
                if pattern is not None:
                    yield pattern, actions
                    pattern = None
                    actions = []
                pattern = values

            elif argtype == ActionAction.ARGTYPE:
                assert pattern is not None
                actions.append(values)

            else:
                raise RuntimeError

        if pattern is not None:
            yield pattern, actions

    def build_re(self, regex):
        if not regex:
            regex = '.*'
        flags = re.I if self.ignore_case else 0
        return re.compile(regex, flags)

    RE_INDENT = re.compile(r'{{}}|{{|}}')
    RE_TOKEN = re.compile(r'"""|\'\'\'|"|\'|#')

    class sub_indent:
        indent = 0

        def __call__(self, m):
            if m.group() == '{{}}':
                pass
            elif m.group() == '{{':
                self.indent += 4
            else:
                self.indent -= 4
                if self.indent < 0:
                    raise ValueError('Indent underflow')
            return '\n' + ' ' * self.indent

    def build_code(self, codes):
        converted = []
        indent = self.sub_indent()
        for code in codes:
            code = ' ' * indent.indent + code + '\n'
            pos = 0
            s = []
            while True:
                m = self.RE_TOKEN.search(code, pos)
                if not m:
                    break
                token_start, token_end = m.span()
                if pos != token_start:
                    s.append(self.RE_INDENT.sub(indent, code[pos:token_start]))
                    pos = token_start

                grp = m.group()
                end_token = '\n' if grp.startswith('#') else grp
                end = re.compile(r'(\\.)|(%s)' % end_token)
                while True:
                    m = end.search(code, token_end)
                    if m:
                        token_end = m.end()
                        if m.group().startswith('\\'):
                            pos = token_end
                            continue
                        else:
                            s.append(code[token_start:token_end])
                            pos = token_end
                            break
                    else:
                        s.append(code[token_start:])
                        pos = len(code)
                        break

            if pos != len(code):
                s.append(self.RE_INDENT.sub(indent, code[pos:]))

            code = ''.join(s)
            converted.append(code)

        result = "\n".join(converted)
        if not result.strip():
            result = 'print(L)'
        
        filename = u"<tse>"
        if six.PY3:
            return compile(result, filename, "exec")

        if not result:
            return None

        enc = self.encoding

        class _Transform(ast.NodeTransformer):

            def visit_Str(self, node):
                if not isinstance(node.s, unicode):
                    s = unicode(node.s, 'utf-8')
                    node.s = s.encode(enc)
                return node

        exprs = ast.parse(result, filename)
        _Transform().visit(exprs)
        return compile(exprs, filename, "exec")


class VarnameDict(collections.defaultdict):
    def __init__(self, varname):
        self.varname = varname
        super(VarnameDict, self).__init__()

    def __missing__(self, key):
        ret = self.varname+str(key)
        self[key] = ret
        return ret


def _run_script(env, input, filename, globals, locals):
    fs = re.compile(env.field_separator) if env.field_separator else None

    FIELD_VARS = VarnameDict('L')
    GROUP_VARS = VarnameDict('S')

    for lineno, line in enumerate(input, 1):
        line = line.rstrip(u"\n")
        for r, c in env.actions:
            m = r.search(line)
            if m:
                S = (m.group(),) + m.groups()
                locals['S'] = S
                for n, s in enumerate(S):
                    locals[GROUP_VARS[n]] = s
                for k, v in m.groupdict().items():
                    locals[k] = v
                locals['M'] = m

                locals['L'] = line

                if fs:
                    locals['L0'] = fs.split(line)
                else:
                    locals['L0'] = line.split()

                for n, s in enumerate(locals['L0'], 1):
                    locals[FIELD_VARS[n]] = s

                locals['N'] = len(locals['L0'])
                locals['LINENO'] = lineno
                locals['FILENAME'] = filename

                six.exec_(c, globals, locals)

                break

def E(cmd):
    return subprocess.check_output(cmd, shell=True, universal_newlines=True)

def run(env):

    locals = globals = {}

    script = ""
    if env.scriptfile:
        try:
            with open(env.scriptfile, "rU") as f:
                script = f.read()
        except IOError:
            pass

    if script:
        six.exec_(script + "\n", globals, locals)

    six.exec_("import sys, os, re", globals, locals)
    six.exec_("from os import path", globals, locals)
    six.exec_("from glob import *", globals, locals)
    try:
        six.exec_("from pathlib import *", globals, locals)
    except ImportError:
        pass

    for _import in env.imports:
        six.exec_("import %s" % _import, globals, locals)

    for _import in env.imports_str:
        six.exec_("from %s import *" % _import, globals, locals)

    globals['E'] = E
    
    if env.begincode:
        six.exec_(env.begincode, globals, locals)

    # todo: clean up followings
    if env.actions:
        if not env.inplace:
            if six.PY2:
                writer = codecs.getwriter(env.outputenc)
                writer.encoding = env.outputenc
                sys.stdout = writer(sys.stdout, env.outputerrors)
            else:
                if hasattr(sys.stdout, 'buffer'):
                    sys.stdout = io.open(os.dup(sys.stdout.buffer.fileno()), 'w', 
                        encoding=env.outputenc, errors=env.outputerrors)

        if not env.files:
            if six.PY2:
                reader = codecs.getreader(env.inputenc)(sys.stdin, env.inputerrors)
            else:
                reader = io.open(os.dup(sys.stdin.buffer.fileno()), 
                    encoding=env.inputenc, errors=env.inputerrors)
            _run_script(env, reader, '<stdin>', globals, locals)
        else:
            for f in env.files:
                stdout = sys.stdout
                if env.inplace:
                    outfilename = '%s%s.%s' % (f, env.inplace, os.getpid())
                    if six.PY2:
                        writer = codecs.getwriter(env.outputenc)
                        writer.encoding = env.outputenc
                        sys.stdout = writer(open(outfilename, 'w'))
                    else:
                        sys.stdout = io.open(
                            outfilename, 'w', encoding=env.outputenc)
                try:
                    with io.open(f, 'r', encoding=env.inputenc, errors=env.inputerrors) as input:
                        _run_script(env, input, f, globals, locals)
                finally:
                    if env.inplace:
                        sys.stdout.close()
                        sys.stdout = stdout

                if env.inplace:
                    shutil.move(f, '%s%s' % (f, env.inplace))
                    shutil.move(outfilename, f)

    if env.endcode:
        six.exec_(env.endcode, globals, locals)

    return locals


class ScriptAction(argparse._StoreAction):

    def __call__(self, parser, namespace, values, option_string=None):
        if not os.path.exists(values) or not os.path.isfile(values):
            raise argparse.ArgumentError(self, "script file does not exist")

        setattr(namespace, self.dest, values)


class StatementAction(argparse._AppendAction):
    ARGTYPE = "statement"

    def __call__(self, parser, namespace, values, option_string=None):
        self._checkValue(parser, namespace, values, option_string)

        items = argparse._copy.copy(
            argparse._ensure_value(namespace, 'statement', []))
        items.append((self.ARGTYPE, values))
        setattr(namespace, 'statement', items)

    def _checkValue(self, parser, namespace, values, option_string):
        return


class PatternAction(StatementAction):
    ARGTYPE = "pattern"

    def _checkValue(self, parser, namespace, values, option_string):
        return


class ActionAction(StatementAction):
    ARGTYPE = "action"

    def _checkValue(self, parser, namespace, values, option_string):
        statements = getattr(namespace, 'statement', None) or []
        for argtype, values in reversed(statements):
            if argtype == PatternAction.ARGTYPE:
                return
            if argtype == StatementAction.ARGTYPE:
                break
        raise argparse.ArgumentError(
            self, "action should be preceded by condition")


def getargparser():
    if six.PY2:
        def argstr(s):
            return six.text_type(s, locale.getpreferredencoding())
    else:
        def argstr(s):
            return str(s)

    parser = argparse.ArgumentParser(description=LOGAPPNAME)
    parser.add_argument(
        '--statement', '-s', action=StatementAction, nargs='+', type=argstr,
        help='a pair of pattern and action(s).', metavar=('PATTERN', 'ACTION'))
    parser.add_argument('--pattern', '-p', action=PatternAction, type=argstr,
                        help='pattern for trailing action(s)')
    parser.add_argument('--action', '-a', action=ActionAction, type=argstr,
                        help='action to be executed.')
    parser.add_argument('--begin', '-b', action='append', nargs='+', type=argstr,
                        help='action invoked before input files have been read.')
    parser.add_argument('--end', '-e', action='append', nargs='+', type=argstr,
                        help='action invoked after input files have been exhausted.')
    parser.add_argument('--ignore-case', '-i', action='store_true',
                        help='ignore case distinctions.')
    parser.add_argument(
        '--field-separator', '-F', action='store', type=argstr,
        help='regular expression used to separate fields.')
    parser.add_argument(
        '--inplace', action='store', type=argstr, metavar='EXTENSION',
        help='edit files in-place.')
    parser.add_argument('--input-encoding', '-ie', action='store', type=argstr,
                        help='encoding of input stream.')
    parser.add_argument(
        '--output-encoding', '-oe', action='store', type=argstr,
        help='encoding of output stream.')
    parser.add_argument(
        '--script-file', '-f', action=ScriptAction, type=argstr,
        help='specifies an alternative script file. the default script file is ~/.tserc.')
    parser.add_argument('--module', '-m', action='append', type=argstr,
                        help='module to be imported.')
    parser.add_argument('--module-star', '-ms', action='append', type=argstr,
                        help='module to be imported in form of "from modname import *".')
    parser.add_argument('FILE', nargs="*", type=argstr,
                        help='With no FILE, or when FILE is -, read standard input.')
    parser.add_argument('--version', action='version',
                        version='%(prog)s 0.0.13')

    return parser


def main():
    parser = getargparser()
    args = parser.parse_args()
    if args.inplace and not args.FILE:
        parser.error("--inplace may not be used with stdin")

    env = Env(
        args.statement, args.begin, args.end, args.input_encoding, args.output_encoding,
        args.module, args.module_star, args.script_file, args.inplace, args.ignore_case,
        args.field_separator, args.FILE)
    run(env)

if __name__ == '__main__':
    main()
