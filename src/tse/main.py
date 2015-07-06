# -*- coding:utf-8 -*-

import sys, argparse, re, locale, ast, codecs, fileinput, os, six, io, shutil

SHORTAPPNAME = "tse"
LOGAPPNAME = "Text Stream Editor in Python"
SCRIPTFILE = os.path.join(os.path.expanduser(u"~"), ".tserc")

class Env:
    actions = ()
    begincode = None
    endcode = None
    inputenc = outputenc = sys.getfilesystemencoding()
    encoding = locale.getpreferredencoding()
    scriptfile = SCRIPTFILE
    
    def __init__(self, statement, begin, end, input_encoding, output_encoding,
            module, module_star, script_file, inplace, files):
        if statement:
            self.actions = [(self.build_re(r), self.build_code(c)) 
                for (r, c) in self._parse_statement(statement)]
        if begin:
            self.begincode = self.build_code("\n".join(begin))
        if end:
            self.endcode = self.build_code("\n".join(end))
        if input_encoding:
            self.inputenc = input_encoding
        if output_encoding:
            self.outputenc = output_encoding
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
                if pattern:
                    yield pattern, "\n".join(actions)
                    pattern = None
                    actions = []
                yield values[0], "\n".join(values[1:])

            elif argtype == PatternAction.ARGTYPE:
                if pattern:
                    yield pattern, "\n".join(actions)
                    pattern = None
                    actions = []
                pattern = values

            elif argtype == ActionAction.ARGTYPE:
                assert pattern
                actions.append(values)

            else:
                raise RuntimeError

        if pattern:
            yield pattern, "\n".join(actions)

    def build_re(self, regex):
        return re.compile(regex)
    
    def build_code(self, code):
        if six.PY3:
            return code

        if not code:
            return None
        enc = self.encoding
        class _Transform(ast.NodeTransformer):
            def visit_Str(self, node):
                if not isinstance(node.s, unicode):
                    s = unicode(node.s, 'utf-8')
                    node.s = s.encode(enc)
                return node

        filename = u"<tse>"
        exprs = ast.parse(code, filename)
        _Transform().visit(exprs)
        return compile(exprs, filename, "exec")

    def _run_script(self, input, filename, globals, locals):
        for lineno, line in enumerate(input, 1):
            line = line.rstrip(u"\n")
            locals['L'] = line
            locals['LINENO'] = lineno
            locals['FILENAME'] = filename
            for r, c in self.actions:
                m = r.search(line)
                if m:
                    S = (m.group(),) + m.groups()
                    locals['S'] = S
                    for n, s in enumerate(S):
                        locals['S'+str(n)] = s
                    for k, v in m.groupdict().items():
                        locals[k] = v
                    locals['M'] = m

                    if c:
                        six.exec_(c, globals, locals)

                    break

    def run(self):

        locals = globals = {}
        
        script = ""
        if self.scriptfile:
            try:
                with open(self.scriptfile, "rU") as f:
                    script = f.read()
            except IOError:
                pass
        
        if script:
            six.exec_(script+"\n", globals, locals)

        six.exec_("import sys, os, re", globals, locals)
        six.exec_("from os import path", globals, locals)
        
        for _import in self.imports:
            six.exec_("import %s" % _import, globals, locals)
        
        for _import in self.imports_str:
            six.exec_("from %s import *" % _import, globals, locals)
        
        if self.begincode:
            six.exec_(self.begincode, globals, locals)
        

        # todo: clean up followings
        if not self.inplace:
            if six.PY2:
                writer = codecs.getwriter(self.outputenc)
                writer.encoding = self.outputenc
                sys.stdout = writer(sys.stdout)
            else:
                if hasattr(sys.stdout, 'buffer'):
                    writer = codecs.getwriter(self.outputenc)
                    sys.stdout = writer(sys.stdout.buffer)

        if not self.files:
            reader = codecs.getreader(self.inputenc)
            self._run_script(reader(sys.stdin), '<stdin>', globals, locals)
        else:
            for f in self.files:
                stdout = sys.stdout
                if self.inplace:
                    outfilename = '%s%s.%s' % (f, self.inplace, os.getpid())
                    if six.PY2:
                        writer = codecs.getwriter(self.outputenc)
                        writer.encoding = self.outputenc
                        sys.stdout = writer(open(outfilename, 'w'))
                    else:
                        writer = codecs.getwriter(self.outputenc)
                        sys.stdout = io.open(outfilename, 'w', encoding=self.outputenc)
                try:
                    with io.open(f, 'r', encoding=self.inputenc) as input:
                        self._run_script(input, f, globals, locals)
                finally:
                    if self.inplace:
                        sys.stdout.close()
                        sys.stdout = stdout

                if self.inplace:
                    shutil.move(f, '%s%s' % (f, self.inplace))
                    shutil.move(outfilename, f)

        if self.endcode:
            six.exec_(self.endcode, globals, locals)
        
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
        
        items = argparse._copy.copy(argparse._ensure_value(namespace, 'statement', []))
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
        raise argparse.ArgumentError(self, "action should be preceded by condition")
        
def getargparser():
    if six.PY2:
        def argstr(s):
            return six.text_type(s, locale.getpreferredencoding())
    else:
        def argstr(s):
            return str(s)

    parser = argparse.ArgumentParser(description=LOGAPPNAME)
    parser.add_argument('--statement', '-s', action=StatementAction, nargs='+', type=argstr,
                        help='a pair of pattern and action(s).', metavar=('PATTERN', 'ACTION'))
    parser.add_argument('--pattern', '-p', action=PatternAction, type=argstr,
                        help='pattern for trailing action(s)')
    parser.add_argument('--action', '-a', action=ActionAction, type=argstr,
                        help='action to be executed.')
    parser.add_argument('--begin', '-b', action='append', type=argstr,
                        help='action invoked before input files have been read.')
    parser.add_argument('--end', '-e', action='append', type=argstr,
                        help='action invoked after input files have been exhausted.')
    parser.add_argument('--inplace', '-i', action='store', type=argstr,
                        help='edit files in-place.')
    parser.add_argument('--input-encoding', '-ie', action='store', type=argstr,
                        help='encoding of input stream.')
    parser.add_argument('--output-encoding', '-oe', action='store', type=argstr,
                        help='encoding of output stream.')
    parser.add_argument('--script-file', '-F', action=ScriptAction, type=argstr,
                        help='specifies an alternative script file. the default script file is ~/.tserc.')
    parser.add_argument('--module', '-m', action='append', type=argstr,
                        help='module to be imported.')
    parser.add_argument('--module-star', '-ms', action='append', type=argstr,
                        help='module to be imported in form of "from modname import *".')
    parser.add_argument('FILE', nargs="*", type=argstr,
                        help='With no FILE, or when FILE is -, read standard input.')
    parser.add_argument('--version', action='version', version='%(prog)s 0.0.3')
    
    return parser

def main():
    parser = getargparser()
    args = parser.parse_args()
    if not args.statement:
        parser.error("statement required")
    if args.inplace and not args.FILE:
        parser.error("--inplace may not be used with stdin")

    env = Env(args.statement, args.begin, args.end, args.input_encoding, args.output_encoding,
            args.module, args.module_star, args.script_file, args.inplace, args.FILE)
    env.run()

if __name__ == '__main__':
    main()

