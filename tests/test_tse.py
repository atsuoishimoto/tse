# -*- coding:utf-8 -*-

import six
import io, unittest, tempfile, os, sys, fileinput
from six import StringIO
import tse.main

class _TestBase(unittest.TestCase):
    def _getParser(self):
        return tse.main.getargparser()
    
    def setUp(self):
        self.testfile = None
        self.testfilename = None
    
    def tearDown(self):
        if self.testfile:
            self.testfile.close()
        if self.testfilename:
            os.unlink(self.testfilename)

        # hack to run test multiple times
        fileinput._state = None
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__

    def _run(self, args, input, enc=None):
        if not enc:
            enc = sys.getfilesystemencoding()

        args = self._getParser().parse_args(args)

        fd, self.testfilename = tempfile.mkstemp()
        self.testfile = io.open(fd, 'w', encoding=enc)
        self.testfile.write(input)
        self.testfile.flush()
        env = tse.main.Env(args.statement, args.begin, args.end, 
            args.input_encoding, args.output_encoding, args.module,
            args.module_star, args.script_file, args.inplace, [self.testfilename])
            
        return env.run()
        
class TestArgs(_TestBase):

    def testStatement(self):
        result = self._getParser().parse_args(
                ["--statement", "arg1", "arg2", 
                 "--statement", "arg3", "arg4", "arg5"])
        self.failUnlessEqual(result.statement, 
                [('statement', ["arg1", "arg2"]),
                 ('statement', ["arg3", "arg4", "arg5"])])

    def testStatementError(self):
        self.failUnlessRaises(SystemExit, self._getParser().parse_args,
                ["--statement"])
        
    def testPatternAction(self):
        result = self._getParser().parse_args(
                ["--pattern", "arg1", 
                 "--action", "arg2", "--action", "arg3"])
        self.failUnlessEqual(result.statement, 
                [('pattern', "arg1"),
                 ('action', "arg2"),
                 ('action', "arg3")])

    def testActionError(self):
        self.failUnlessRaises(SystemExit, self._getParser().parse_args,
                ["--action", "arg1", ])
        self.failUnlessRaises(SystemExit, self._getParser().parse_args,
                ["--action", "arg1", "--action", "arg2", ])

class TestExec(_TestBase):
    def testBegin(self):
        globals = self._run(["-b", "a=100", "-b", "b=200"], u"")
        self.failUnlessEqual(globals['a'], 100)
        self.failUnlessEqual(globals['b'], 200)

    def testEnd(self):
        globals = self._run(["-e", "a=100", "-e", "b=200"], u"")
        self.failUnlessEqual(globals['a'], 100)
        self.failUnlessEqual(globals['b'], 200)

    def testStatement(self):
        globals = self._run(["-b" "lines=[]", "-s", "\w+", "lines.append(L)"], u"abc\n----\ndef\n")
        self.failUnlessEqual(globals['lines'], ["abc", "def"])
        
    def testPattern(self):
        globals = self._run(["-p", "\w+", "-p", "\w+"], u"abc\n----\ndef\n")
        
    def testAction(self):
        globals = self._run(["-b" "lines=[]", "-p", "\w+", "-a", "lines.append(L)"], u"abc\n----\ndef\n")
        self.failUnlessEqual(globals['lines'], ["abc", "def"])
        
    def testModule(self):
        globals = self._run(["-m", "unicodedata", "-m", "datetime as ddd", "-s", "\w+"], u"abc\n----\ndef\n")
        import unicodedata, datetime
        self.failUnlessEqual(globals['unicodedata'], unicodedata)
        self.failUnlessEqual(globals['ddd'], datetime)
        
    def testModuleStar(self):
        globals = self._run(["-ms", "unicodedata", "-s", "\w+"], u"abc\n----\ndef\n")
        import unicodedata, datetime
        self.failUnlessEqual(globals['name'], unicodedata.name)

    def testScriptFile(self):
        fd, filename = tempfile.mkstemp()
        testfile = os.fdopen(fd, "w")
        try:
            testfile.write("script_a=100")
            testfile.close()
            
            globals = self._run(["-s", "\w+", "-F", filename], u"")
            self.failUnlessEqual(globals['script_a'], 100)
        finally:
            os.unlink(filename)

class TestEncoding(_TestBase):
    def testInput(self):
        globals = self._run(["-s", ".*", "a=L", "-ie", "euc-jp"], u"\N{HIRAGANA LETTER A}",
            enc='euc-jp')
        self.failUnlessEqual(globals['a'], u"\N{HIRAGANA LETTER A}")
        
    def testOutput(self):
        sys.stdout = out = StringIO()
        globals = self._run(
            ["-s", ".*", "print(u'\\N{HIRAGANA LETTER I}')", 
             "-ie", "euc-jp", "-o", "euc-jp"], 
            u"\N{HIRAGANA LETTER I}", enc='euc-jp')

        ret = out.getvalue()[:-1]
        if six.PY3:
            ret = ret.encode('euc_jp')
        self.failUnlessEqual(ret, u"\N{HIRAGANA LETTER I}".encode('euc-jp'))
        

class TestInplace(_TestBase):
    def testInplace(self):
        self._run(["-s", ".*", "print(u'\N{HIRAGANA LETTER I}')", "-i", ".bak"],
            u"\N{HIRAGANA LETTER A}")
        self.failUnlessEqual(open(self.testfilename, 'rb').read()[:-1],
            u"\N{HIRAGANA LETTER I}".encode('utf-8'))
        self.failUnlessEqual(open(self.testfilename+'.bak', 'rb').read(),
            u"\N{HIRAGANA LETTER A}".encode('utf-8'))
        os.unlink(self.testfilename+'.bak')


class TestIndent(_TestBase):
    def testIndent(self):
        sys.stdout = out = StringIO()
        self._run(["-s", ".*", 
            "for c in L:{{if ord(c) % 2:{{print(c)}}else:{{print(c*2)}}}}"],
            u"abcdefg")

        ret = out.getvalue()[:-1]
        self.failUnlessEqual(ret, 'a\nbb\nc\ndd\ne\nff\ng')

if __name__ == '__main__':
    unittest.main()

