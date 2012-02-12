tse - Python Stream Scripting
=============================

tse processes text input stream with Python expressions. Like AWK, tse command line option is a series of pair of condition and action:

    tse -p COND1 -a ACTION1 -p COND2 -p ACTION2 -a ACTION3

or 

    tse -s COND1 ACTION1 -s COND2 ACTION2 ACTION3

For example, to find lines starts with 'abc' ::

    tse -p "^abc" -a "print L"

to find line contains URL ::

    tse -s "http://\\S+" "print S0"  -s "mailto://\\S+" "print S0" 

to convert upper case ::

    tse -p ".*" -a "print L.upper()"

::

  usage: tse [-h] [--statement PATTERN [ACTION ...]] [--pattern PATTERN]
             [--action ACTION] [--begin BEGIN] [--end END]
             [--input-encoding INPUT_ENCODING]
             [--output-encoding OUTPUT_ENCODING] [--script-file SCRIPT_FILE]
             [--module MODULE] [--module-star MODULE_STAR]
             [FILE [FILE ...]]
  
  Text Stream Editor in Python
  
  positional arguments:
    FILE                  With no FILE, or when FILE is -, read standard input.
  
  optional arguments:
    -h, --help            show this help message and exit
    --statement PATTERN [ACTION ...], -s PATTERN [ACTION ...]
                          a pair of pattern and action(s).
    --pattern PATTERN, -p PATTERN
                          pattern for trailing action(s)
    --action ACTION, -a ACTION
                          action to be executed.
    --begin BEGIN, -b BEGIN
                          action invoked before input files have been read.
    --end END, -e END     action invoked after input files have been exhausted.
    --input-encoding INPUT_ENCODING, -ie INPUT_ENCODING
                          encoding of input stream.
    --output-encoding OUTPUT_ENCODING, -oe OUTPUT_ENCODING
                          encoding of output stream.
    --script-file SCRIPT_FILE, -F SCRIPT_FILE
                          specifies an alternative script file. the default
                          script file is ~/.tserc.
    --module MODULE, -m MODULE
                          module to be imported.
    --module-star MODULE_STAR, -ms MODULE_STAR
                          module to be imported in form of "from modname import
                          *".
  
  
Variables
---------

Following variables can be used within action statement.

:variable: values

:sys: Python sys module

:os: Python os module

:path: Python os.path module

:re: python re module

:FILENAME: The name of file currently reading.

:LINENO: Line numberof the current line.

:L: Current line.

:S: Part of Text matched to condition regex.

:S0, S1, ...: sub-string matched to condition regex. S0 is entire matched part, S1, S2 are sub group of condition regex.

:(name): If condition regex has group names defined by '(?P<name>)', sub-string could be referenced by variable 'name'.

:M: Match object


Script file
-----------

If the file ~/.tserc exists, the file is execused at beginning. In the script file, you can import your faivorite modules, or write convenient functions you like. The values defined in the scipt file are accessible by actions specifyed in command options.


Examples
--------

Print sum of numeric characters in an each line of input stream::

    tse -s "\d+" "print(sum(int(s) for s in re.findall(r"\d+", L)))"


Sum all numeric characters in all lines::

    tse -b "all=0" \
         -s "\d+" "all+=sum(int(s) for s in re.findall(r"\d+", L)))" \
         -e "print(all)"

Find all extention parts in current directory::

    find . | tse -s ".*" "print path.splitext(L)[1]"

