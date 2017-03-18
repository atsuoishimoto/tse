
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

\ 

Command line options
-----------------------


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
    --ignore-case, -i     ignore case distinctions.
    --field-separator FIELD_SEPARATOR, -F FIELD_SEPARATOR
                        regular expression used to separate fields.
    --inplace EXTENSION   edit files in-place.
    --input-encoding INPUT_ENCODING, -ie INPUT_ENCODING
                          encoding of input stream.
    --output-encoding OUTPUT_ENCODING, -oe OUTPUT_ENCODING
                          encoding of output stream.
    --script-file SCRIPT_FILE, -f SCRIPT_FILE
                          specifies an alternative script file. the default
                          script file is ~/.tserc.
    --module MODULE, -m MODULE
                          module to be imported.
    --module-star MODULE_STAR, -ms MODULE_STAR
                          module to be imported in form of "from modname import *".
  
Patterns and Actions
-----------------------

Pattern is a regular expression to search line. Action is executed when corresponding pattern is found in the line. If a pattern is matched, following pattern/action pairs are not execused.

Empty pattern means '.\*', and empty action means 'print(L)'.

Action arguments in the same pattern are joined with '\n'. So, you can write

::

    tse -p '.*' -a 'for c in L:' -a '    print(c)'

    tse -s '.*' 'for c in L:' '    print(c)'



'\{\{' and '\}\}' in the action are converted to newline + indent/dedent. For example, 

::

    'if L1:{{for c in L2:{{print(c)}}else:{{print(L3)}}}}else:{{print(L4)}}'

is converted to 

::

    if L1:
        for c in L2:
            print(c)
        else:
            print(L3)
    else:
        print(L4)

'{{' and '}}' in the string literal and comments are ignored.

Variables
---------

Following variables are can be used within action statement.

:FILENAME: The name of file currently reading.

:LINENO: Line numberof the current line.

:L: Current line.

:L0: Current line.

:L1, L2: Fields of the current line separeted by whitespace.

:N: Number of fileds.

:S: Part of Text matched to condition regex.

:S0, S1, ...: sub-string matched to condition regex. S0 is entire matched part, S1, S2 are sub group of condition regex.

:(name): If condition regex has group names defined by '(?P<name>)', sub-string could be referenced by variable 'name'.

:M: Match object.

:E: Function to call subprocess.check_output(). ``E('ls ~')`` is equevalent to ``subprocess.check_output('ls ~', shell=True, universal_newline=True)``.

Pre-imported modules
---------------------

Following modules are imported as follows::

    import sys, os, re
    from os import path
    from glob import *
    from pathlib import *  # Only if pathlib is installed.


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

