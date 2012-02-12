# -*- coding:utf-8 -*-

import sys, argparse, re, locale, ast, codecs, fileinput, os

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
            module, module_star, script_file, files):
        if statement:
            self.actions = [(self.build_re(r), self.build_code(c)) for (r, c) in self._parse_statement(statement)]
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
        regex = unicode(regex, self.encoding)
        return re.compile(regex)
    
    def build_code(self, code):
        if not code:
            return None

        enc = self.encoding
        class _Transform(ast.NodeTransformer):
            def visit_Str(self, node):
                if not isinstance(node.s, unicode):
                    s = unicode(node.s, 'utf-8')
                    node.s = s.encode(enc)
                return node

        filename = "<tse>"
        src = unicode(code, enc)
        exprs = ast.parse(code, filename)
        _Transform().visit(exprs)
        return compile(exprs, filename, "exec")

    def run(self):

        writer = codecs.getwriter(self.outputenc)
        reader = codecs.getreader(self.inputenc)
        sys.stdout = writer(sys.stdout)
        
        sys.stdout.encoding = self.outputenc
        sys.stdin = reader(sys.stdin)

        locals = {}
        globals = {}
        
        script = ""
        if self.scriptfile:
            try:
                with open(self.scriptfile, "rU") as f:
                    script = f.read()
            except IOError:
                pass
        
        if script:
            exec script+"\n" in locals, globals

        exec "import sys, os, re" in locals, globals
        exec "from os import path" in locals, globals
        
        for _import in self.imports:
            exec "import %s" % _import in locals, globals
        
        for _import in self.imports_str:
            exec "from %s import *" % _import in locals, globals
        
        if self.begincode:
            exec self.begincode in locals, globals
        
        def openhook(filename, mode):
            return reader(open(filename, mode))

        lines = fileinput.input(self.files, openhook=openhook)
        for line in lines:
            line = line.rstrip(u"\n")
            locals['L'] = line
            locals['LINENO'] = lines.lineno()
            locals['FILENAME'] = lines.filename()
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
                        exec c in locals, globals

                    break
            
        if self.endcode:
            exec self.endcode in locals, globals
        
        return locals, globals

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
    parser = argparse.ArgumentParser(description=LOGAPPNAME)
    parser.add_argument('--statement', '-s', action=StatementAction, nargs='+',
                        help='a pair of pattern and action(s).', metavar=('PATTERN', 'ACTION'))
    parser.add_argument('--pattern', '-p', action=PatternAction,
                        help='pattern for trailing action(s)')
    parser.add_argument('--action', '-a', action=ActionAction, 
                        help='action to be executed.')
    parser.add_argument('--begin', '-b', action='append',
                        help='action invoked before input files have been read.')
    parser.add_argument('--end', '-e', action='append',
                        help='action invoked after input files have been exhausted.')
    parser.add_argument('--input-encoding', '-ie', action='store',
                        help='encoding of input stream.')
    parser.add_argument('--output-encoding', '-oe', action='store',
                        help='encoding of output stream.')
    parser.add_argument('--script-file', '-F', action=ScriptAction,
                        help='specifies an alternative script file. the default script file is ~/.tserc.')
    parser.add_argument('--module', '-m', action='append',
                        help='module to be imported.')
    parser.add_argument('--module-star', '-ms', action='append',
                        help='module to be imported in form of "from modname import *".')
    parser.add_argument('FILE', nargs="*",
                        help='With no FILE, or when FILE is -, read standard input.')
    parser.add_argument('--version', action='version', version='%(prog)s 0.0.3')
    
    return parser

def main():
    parser = getargparser()
    args = parser.parse_args()
    if not args.statement:
        parser.error("statement required")

    env = Env(args.statement, args.begin, args.end, args.input_encoding, args.output_encoding,
            args.module, args.module_star, args.script_file, args.FILE)
    env.run()

if __name__ == '__main__':
    main()

