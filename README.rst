
tse - Python Stream Scripting
=============================

Tse processes text input stream with Python expressions. Like AWK, tse command line option is a series of pair of condition and action:

    tse -s COND1 ACTION1 -s COND2 ACTION2 ACTION3

For example, to find lines starts with ``abc`` ::

    $ tse -s '^abc' 'P(L)' -- *.*

to find line contains URL ::

    $ tse -s 'http://\\S+' 'P(S0)'  -s 'mailto://\\S+' 'print S0'  \
        -- *.*

to convert upper case ::

    $ cat FILENAME | tse -p '.*' -a 'P(L.upper())'

Also, tse can be used to execute Python one-liner.

To get current directory ::

    $ tse -x 'P(os.getcwd())'

To celebrate the Friday ::

    $ tse -ms datetime -x 'if 4==date.today().weekday():' \
                          '{{P("Thank God It'\''s Friday")}}'


\ 

Command line options
-----------------------


::

  usage: tse [-h] [--statement PATTERN [ACTION ...]]
             [--execute EXECUTE [EXECUTE ...]] [--begin BEGIN [BEGIN ...]]
             [--end END [END ...]] [--ignore-case]
             [--field-separator FIELD_SEPARATOR] [--inplace EXTENSION]
             [--input-encoding INPUT_ENCODING]
             [--output-encoding OUTPUT_ENCODING] [--script-file SCRIPT_FILE]
             [--module MODULE] [--module-star MODULE_STAR] [--version]
             [FILE [FILE ...]]
  
  Text Stream Editor in Python
  
  positional arguments:
    FILE                  With no FILE, or when FILE is -, read standard input.
  
  optional arguments:
    -h, --help            show this help message and exit
    --statement PATTERN [ACTION ...], -s PATTERN [ACTION ...]
                          a pair of pattern and action(s).
    --execute EXECUTE [EXECUTE ...], -x EXECUTE [EXECUTE ...]
                          execute script without reading files.
    --begin BEGIN [BEGIN ...], -b BEGIN [BEGIN ...]
                          action invoked before input files have been read.
    --end END [END ...], -e END [END ...]
                          action invoked after input files have been exhausted.
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
                          modules to be imported.
    --module-star MODULE_STAR, -ms MODULE_STAR
                          modules to be imported in form of "from modname import
                          *".
    --version             show program's version number and exit

  
Patterns and Actions
-----------------------

The ``--statement`` option accepts a pattern and actions.

Pattern is a regular expression to search line. Action is executed when corresponding pattern is found in the line. This command prints lines contains "abc" in the FILENAME.

::

    $ cat FILENAME | tse -s "abc" "print(L)"


If a pattern is matched, following pattern/action pairs are not execused. This command prints lines not starts with `#` in the FILENAME.

::

    $ cat FILENAME | tse -s "'#" "pass" ".*" "P(L)"


Empty pattern means ``.\*``, and empty action means ``print(L)``. So, ``tse -s '' ''`` is equivalent to ``tse -s '.*' 'P(L)'``

Action arguments in a ``--statement`` option are joined with ``\n``. So, you can write

::

    tse -s '.*' 'for c in L:' '    print(c)'



``{{`` and ``}}`` in the action are converted to newline + indent/dedent. For example, 

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

``{{`` and ``}}`` in the string literal and comments are ignored.


--execute option
-----------------------

Python script specified with ``--execute`` option is execused without reading input file. This can be used as Python one-liner executer.

::

   # sample to post message to Discord chat
   $ tse -ms requests -x 'P(post("https://discordapp.com/api/webhooks/XXX/YYY",'\
                       'json=dict(username="username", content="test")))'


--begin and --end option
------------------------------------

Python script specified with ``--begin`` option is execused before input streams are read. Python script specified with ``--end`` option is execused after input streams are exhausted.


::
    # sample to count all letters of the files in the directory
    $ tse --begin 'n=0' --end 'P(n)' -s '' 'n+=len(L)' -- *.*


Variables
---------

Following variables are can be used within action statement.

:FILENAME: The name of file currently reading.

:F: The `pathlib.Path <https://docs.python.org/3/library/pathlib.html#concrete-paths>`__ object of the file currently reading.

:LINENO: Line numberof the current line.

:L: Current line.

:L0: Current line.

:L1, L2: Fields of the current line separeted by whitespace.

:N: Number of fileds.

:S: Part of text matched to condition regex.

:S0, S1, ...: sub-string matched to condition regex. S0 is entire matched part, S1, S2 are sub group of condition regex.

:(name): If condition regex has group names defined by ``(?P<name>)``, sub-string could be referenced by variable ``name``.

:M: Match object.

:E: Function to call subprocess.check_output(). ``E('ls ~')`` is equevalent to ``subprocess.check_output('ls ~', shell=True, universal_newline=True)``.

:P: (Python3 only) Function to call print(). ``P('STRING')`` is equevalent to ``print('STRING')``.

:C: The `pathlib.Path <https://docs.python.org/3/library/pathlib.html#concrete-paths>`__ object of the current directory.


Pre-imported modules
---------------------

Following modules are imported as follows::

    import sys, os, re
    from os import path
    from glob import *
    from pathlib import *  # Only if pathlib is installed.


Script file
-----------

If the file ``~/.tserc`` exists, the file is execused at beginning. In the script file, you can import your faivorite modules, or write convenient functions you like. The values defined in the scipt file are accessible by actions specifyed in command options.


Command substitution
----------------------

In Python3, string within backticks are executed as command. The string **\`ls ~\`** is equivaent to ``subprocess.check_output('ls ~', shell=True, universal_newline=True)``.

In Python 3.6 or later, ``f`` prefix is supported::

    ls | tse -s '\.txt' 'P(f`cat {L}`)'


Examples
--------

Print sum of numeric characters in an each line of input stream::

    tse -s "\d+" \
         "print(sum(int(s) for s in re.findall(r"\d+", L)))" \
         -- *.*


Sum all numeric characters in all lines::

    tse -b "all=0" \
         -s "\d+" "all+=sum(int(s) for s in re.findall(r"\d+", L)))" \
         -e "P(all)"
         -- *.*

Find all extension parts in current directory::

    ls | tse --begin 'exts=set()' --end 'P(exts)' \
         -s '' 'exts.add(Path(L).suffix)'

