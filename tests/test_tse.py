# -*- coding:utf-8 -*-

import six
import io
import unittest
import tempfile
import os
import sys
import fileinput
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
        env = tse.main.Env(args.execute, args.statement, args.begin, args.end,
                           args.input_encoding, args.output_encoding, args.module,
                           args.module_star, args.script_file, args.inplace, args.ignore_case,
                           args.field_separator, [self.testfilename])

        return tse.main.run(env)


class TestArgs(_TestBase):

    def testStatement(self):
        result = self._getParser().parse_args(
            ["--statement", "arg1", "arg2",
             "--statement", "arg3", "arg4", "arg5"])
        self.assertEqual(result.statement,
                             [('statement', ["arg1", "arg2"]),
                              ('statement', ["arg3", "arg4", "arg5"])])

    def testStatementError(self):
        self.assertRaises(SystemExit, self._getParser().parse_args,
                              ["--statement"])

    def testPatternAction(self):
        result = self._getParser().parse_args(
            ["--pattern", "arg1",
             "--action", "arg2", "--action", "arg3"])
        self.assertEqual(result.statement,
                             [('pattern', "arg1"),
                              ('action', "arg2"),
                                 ('action', "arg3")])

    def testActionError(self):
        self.assertRaises(SystemExit, self._getParser().parse_args,
                              ["--action", "arg1", ])
        self.assertRaises(SystemExit, self._getParser().parse_args,
                              ["--action", "arg1", "--action", "arg2", ])


class TestExec(_TestBase):

    def testBegin(self):
        globals = self._run(["-b", "a=100", "b=200"], u"")
        self.assertEqual(globals['a'], 100)
        self.assertEqual(globals['b'], 200)

    def testEnd(self):
        globals = self._run(["-e", "a=100", "b=200"], u"")
        self.assertEqual(globals['a'], 100)
        self.assertEqual(globals['b'], 200)

    def testExecute(self):
        sys.stdout = out = StringIO()
        globals = self._run(["-x", "a=100", "if a:", "{{print(a)"], u"")
        self.assertEqual(sys.stdout.getvalue(), "100\n")

    def testStatement(self):
        globals = self._run(
            ["-b", "lines=[]", "-s", "\\w+", "lines.append(L)"], u"abc\n----\ndef\n")
        self.assertEqual(globals['lines'], ["abc", "def"])

    def testAction(self):
        globals = self._run(
            ["-b", "lines=[]", "-p", "\\w+", "-a", "lines.append(L)"], u"abc\n----\ndef\n")
        self.assertEqual(globals['lines'], ["abc", "def"])

    def testIgnorecase(self):
        globals = self._run(
            ["-i", "-b" "lines=[]", "-p", "a", "-a", "lines.append(L)"], u"abc\nAbc\n123\n")
        self.assertEqual(globals['lines'], ["abc", "Abc"])

    def testModule(self):
        globals = self._run(
            ["-m", "unicodedata, bisect", "-m", "datetime as ddd", "-s", "\\w+"], u"abc\n----\ndef\n")
        import unicodedata
        import datetime
        import bisect
        self.assertEqual(globals['unicodedata'], unicodedata)
        self.assertEqual(globals['ddd'], datetime)
        self.assertEqual(globals['bisect'], bisect)

    def testModuleError(self):
        self.assertRaises(SystemExit, self._getParser().parse_args,
                         ["-m", "unicodedata;", "-s", "\\w+"])

    def testModuleStar(self):
        globals = self._run(
            ["-ms", "unicodedata, bisect", "-s", "\\w+"], u"abc\n----\ndef\n")
        import unicodedata
        import datetime
        import bisect
        self.assertEqual(globals['name'], unicodedata.name)
        self.assertEqual(globals['bisect'], bisect.bisect)

    def testModuleStarError(self):
        self.assertRaises(SystemExit, self._getParser().parse_args,
                         ["-ms", "unicodedata;", "-s", "\\w+"])

    def testScriptFile(self):
        fd, filename = tempfile.mkstemp()
        testfile = os.fdopen(fd, "w")
        try:
            testfile.write("script_a=100")
            testfile.close()

            globals = self._run(["-s", "\\w+", "-f", filename], u"")
            self.assertEqual(globals['script_a'], 100)
        finally:
            os.unlink(filename)

    def testShell(self):
        globals = self._run(["-e", "a=E('echo abc')"], u"")
        self.assertEqual(globals['a'], 'abc\n')

class TestEncoding(_TestBase):

    def testInput(self):
        globals = self._run(
            ["-s", ".*", "a=L", "-ie", "euc-jp"], u"\N{HIRAGANA LETTER A}",
            enc='euc-jp')
        self.assertEqual(globals['a'], u"\N{HIRAGANA LETTER A}")

    def testOutput(self):
        sys.stdout = out = StringIO()
        globals = self._run(
            ["-s", ".*", "print(u'\\N{HIRAGANA LETTER I}')",
             "-ie", "euc-jp", "-o", "euc-jp"],
            u"\N{HIRAGANA LETTER I}", enc='euc-jp')

        ret = out.getvalue()[:-1]
        if six.PY3:
            ret = ret.encode('euc_jp')
        self.assertEqual(ret, u"\N{HIRAGANA LETTER I}".encode('euc-jp'))


class TestInplace(_TestBase):

    def testInplace(self):
        self._run(
            ["-s", ".*", "print(u'\N{HIRAGANA LETTER I}')",
             "--inplace", ".bak"],
            u"\N{HIRAGANA LETTER A}")
        self.assertEqual(open(self.testfilename, 'rb').read(),
                             u"\N{HIRAGANA LETTER I}\n".encode('utf-8'))
        self.assertEqual(open(self.testfilename + '.bak', 'rb').read(),
                             u"\N{HIRAGANA LETTER A}".encode('utf-8'))
        os.unlink(self.testfilename + '.bak')


class TestSeparator(_TestBase):

    def testSeparator(self):
        globals = self._run(
            ["-s", ".*", "a=L0", "-F", "\\t"], u" A B C\tD\tE\tF ")
        self.assertEqual(globals['a'], [u" A B C", u"D", u"E", u"F "])

        globals = self._run(
            ["-s", ".*", "a=L0"], u"   A B C\tD\tE\t F    ")
        self.assertEqual(globals['a'], [u"A", u"B", u"C", u"D", u"E", u"F"])


class TestIndent(_TestBase):

    def testIndent(self):
        sys.stdout = out = StringIO()
        self._run(["-s", ".*",
                   "for c in L:{{if ord(c) % 2:{{print(c)}}else:{{print(c*2)}}}}"],
                  u"abcdefg")

        ret = out.getvalue()[:-1]
        self.assertEqual(ret, 'a\nbb\nc\ndd\ne\nff\ng')

    def testNewline(self):
        sys.stdout = out = StringIO()
        self._run(["-s", ".*",
                   "if 1:{{print(1){{}}print(2)}}"],
                  u"abcdefg")

        ret = out.getvalue()[:-1]
        self.assertEqual(ret, '1\n2')

    def testMultiline(self):
        for opt in [["-s", ".*"], ["-b"], ["-e"]]:
            sys.stdout = out = StringIO()
            self._run(opt + ["for i in range(1):{{", "print(i)", "}}"],
                      u"abcdefg")

            ret = out.getvalue()
            self.assertEqual(ret, '0\n')

class TestString(_TestBase):
    def testString(self):
        sys.stdout = out = StringIO()
        self._run(["-s", ".*",
                   'print("abcdefg\\\"")'],
                  u"abcdefg")

        ret = out.getvalue()[:-1]
        self.assertEqual(ret, 'abcdefg"')

    def testCommand(self):
        sys.stdout = out = StringIO()
        self._run(["-s", ".*",
                   'print(`echo 12345`)'],
                  u"abcdefg")

        ret = out.getvalue()[:-1]
        self.assertEqual(ret, '12345\n')

    def testfCommand(self):
        sys.stdout = out = StringIO()
        self._run(["-s", ".*",
                   'print(f`echo {L}`)'],
                  u"abcdefg")

        ret = out.getvalue()[:-1]
        self.assertEqual(ret, 'abcdefg\n')


if __name__ == '__main__':
    unittest.main()
