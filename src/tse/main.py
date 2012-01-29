# -*- coding:utf-8 -*-

import sys, argparse, re, locale, ast, codecs, fileinput

SHORTAPPNAME = "tse"
LOGAPPNAME = "Text Stream Editor in Python"

class Env:
    actions = ()
    begincode = None
    endcode = None
    inputenc = outputenc = sys.getfilesystemencoding()
    encoding = locale.getpreferredencoding()
    
    def __init__(self, action, begin, end, input_encoding, output_encoding, module, module_star, files):
        if action:
            self.actions = [(self.build_re(r), self.build_code(c)) for (r, c) in action]
        if begin:
            self.begincode = self.build_code("\n".join(begin))
        if end:
            self.endcode = self.build_code(end)
        if input_encoding:
            self.inputenc = input_encoding
        if output_encoding:
            self.outputenc = outout_encoding
        self.imports = module or ()
        self.imports_str = module_star or ()
        self.files = files or ()
    
    def build_re(self, regex):
        regex = unicode(regex, self.encoding)
        return re.compile(regex)
    
    def build_code(self, code):
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
        locals = {}
        globals = {}
        
        exec "import sys, os, re" in locals, globals
        exec "from os import path" in locals, globals
        
        for _import in self.imports:
            exec "import %s" % _import in locals, globals
        
        for _import in self.imports_str:
            exec "from %s import *" % _import in locals, globals
        
        sys.stdout = codecs.getwriter(self.outputenc)(sys.stdout)
        sys.stdin = codecs.getreader(self.inputenc)(sys.stdin)
        
        if self.begincode:
            exec self.begincode in locals, globals

        lines = fileinput.input(self.files)
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

                    exec c in locals, globals

                    break
            
        if self.endcode:
            exec self.endcode in locals, globals
        
def getargparser():
    parser = argparse.ArgumentParser(description=LOGAPPNAME)
    parser.add_argument('--action', '-a', action='append', nargs=2,
                        help='pair of condition and action.')
    parser.add_argument('--begin', '-b', action='append',
                        help='action invoked before input files have been read.')
    parser.add_argument('--end', '-e', action='append',
                        help='action invoked after input files have been exhausted.')
    parser.add_argument('--input-encoding', '-ie', action='store',
                        help='encoding of input stream.')
    parser.add_argument('--output-encoding', '-oe', action='store',
                        help='encoding of output stream.')
    parser.add_argument('--module', '-m', action='append',
                        help='module to be imported.')
    parser.add_argument('--module-star', '-ms', action='append',
                        help='module to be imported in form of "from modname import *".')
    parser.add_argument('files', nargs="*",
                        help='file names to be read. if files are omitted, stdin would be used.')
    
    return parser

def main():
    parser = getargparser()
    args = parser.parse_args()
    env = Env(**args.__dict__)
    env.run()

if __name__ == '__main__':
    main()

