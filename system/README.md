# Carneades Argument Evaluation System (CAES) in Python
Requirements for the second coursework for INFR09043 Artificial Intelligence Large Practical ([AILP](http://www.inf.ed.ac.uk/teaching/courses/ailp/)) 2016/17 are:

- [4.1](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#4) Implementing file-reading capability
- [4.2](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Devising a syntax
- [4.3](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Deserialisation
- [4.4](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Provide examples


## Getting around this file:
Sections for this documentation includes:
* [Directory of folders](#directory)
* [Setting up the `ailp_env` virtual environment](#setup)
* [Instructions for testing the system](#demo)
* [Syntax for `.yml` files](#syntax)
* [Running regression test](#testing)

-------

Overview
======
The user will create a file to contain all the statements (propositions), arguments, proofstandard and parameters required for CAES. The extension for the file is `.yml`. It is recommended that the file is stored alongside the `src` folder, for instance in the `samples` folder.

A general workflow:

1. User creates file for arguments, e.g. `caes.yml`
2. Setup virual environment - `ailp_env`
3. Either:
..* Start the python interpreter and import `carneades` (see [running from the interpreter](#Interpreter))
..* Run from the command line
4. The file will go through lexical analysis to ensure [synatx](#syntax) is correct and tokenize the files, then parsing it.
5. The will be used as python arguments for `caes.py` program.

## Directory
The directory of the files is as such:
```
system
|   README.md
└───src
|   └───carneades
|       |   caes.py
|       |   reader.py
|       |   generateTokens.py
|       |   parser.py
|       |   error.py
|       |   caes.doctest.py
|       |   tracecalls.py
|      
└───samples
|   |
|   |
|
└───ailp_env
    └───bin
        |   activate
        |   ...

```
## Setup

### `ailp_env` virtual environment
Need to activate the `ailp_env` before running the code (assumed is done; commands are listed below):
```$
[From the system folder]
$ source ailp_env/bin/activate
(ailp_env) $  # the environment name should appear on each line in terminal
```
User should refer to the assignemtn document for a more detailed documentation.

## Demo

### How to run
There is a few mode supported for this running CAES:
* Single file
* Multiple files
* All `.yml` files in a directory

#### Single or multiple files
Assuming your source files are in the `system/samples` folder:
```$
(ailp_env) $
(ailp_env) $
(ailp_env) $
```
#### Running CAES on an entire directory
```$
(ailp_env) $
(ailp_env) $
(ailp_env) $
```

## Syntax for `.yml` files
The syntax for the files are inspired from YAML, hence the extension name. YAML is a user friendly markdown language which does not have too many hierachical elements (such as brackets). The syntax rules are strict, and will throw up any error if it is not well followed. Syntax for caes illustrates the essential elements required for each caes.

### Rules:
1. Spaces and newlines are delimiters. Usage of tab will throw errors. (unless your editor converts them to 'soft tabs' - space)
2. the standard indent size is `2`. Similar to python, indents determine the grouping of statements, which allowes us to compute the nesting of maps and sequences, if any.
3. Special characters: `:`, `-`, `~` are not allowed as individual tokens, unless they are used to define sequence or map. They can be used after any `CHAR` as long as it is before a white space.

```
INDENT = '  '
SPECIAL_CHAR = ':' | '-' | '~'
CHAR ::= [abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789]
STMT ::= ' 'CHAR[CHAR | SPECIAL_CHAR]*' '  # bounded by whitespace(' ')
STMTS ::= SEQUENCES | MAPS | COMMENT

COMMENT ::= '#'[CHAR]*  # Everything after '#' will be ignored

SEQUENCES ::= STMT[STMT]* ' : ' [SEQUENCE_ELEMENT | SEQUENCES]*
SEQUENCE_ELEMENT ::= [INDENT]* '- ' STMTS   # each SEQUENCE_ELEMENT must start on a newline, if it a nested sequence, indents are used to infer group membership

MAPS ::= STMT[STMT]* ':' [MAP_ELEMENT | MAPS]*
MAP_ELEMENT ::= INDENT[INDENT]* STMTS   # each MAP_ELEMENT must start on a new line, and must have an indent set the key (in previous line) to the elements
```

### Examples
* Sequence
A sequnce is similar to `list()` in python.

```
# a simple sequence
- kill # the indent level follows the location of the key (ASSUMPTION here)
- witness1
- witness2
- unreliable1

- Ground Level 1 :
  - First level 11
  - First level 12
- Ground Level 2 : # once the indent level drops, inferred as a new sequence
  - First level 21
  - ...
```

* Maps
A map is similar to `dict()` in python:

```
ASSUMPTION: # simple
  kill

ASSUMPTION: # mapping ASSUMPTION to a list
  - kill
  - witness1
  - wintess2
  - unreliable1

PARAMETER: # PARAMETERS have a value with 3 maps
  alpha :   # this is same as the simple map
    0.4     # double indent to denote membership to 'alpha'
  beta :
    0.2
  gamma :
    0.10
```

###  Syntax for CAES
These fields must be present in order for an argument graph to be presented

* `PROPOSITION`
..* Begin with 'PROPOSITION'
..* A sequence of map; each map is a proposition uniquely identified by `PROP_ID`. the `polarity` is a compulsory field. The polarity indicates the falsehood of the proposition.
```
PROPOSITION :
  - <PROP_ID> :
      text : <elaboration of proposition>
      polarity : <True, False>

  # EXAMPLE:
  - ID CAN HAVE SPACES :
      text : this is an example
      polarity : True
```

* `ASSUMPTION`
..* Begin with 'ASSUMPTION'
..* A sequence of `PROP_ID` defined in `PROPOSITION`
```
ASSUMPTION :
  - <PROP_ID>

  # EXAMPLE
  - ID CAN HAVE SPACES
```

* `ARGUMENT`
..* Begins in with 'ARGUMENT'
..* A sequence of map, with `ARG_ID` as key. Each map consist of the following maps: `premise`, `exception`, `conclusions`, `weight`
```
ARGUMENT :
  - <ARG_ID> :
    premise :  # premise is a sequence
      - <PROP_ID>
    exception : # exception is a sequence
      - <PROP_ID>
    conclusion:
      <PROP_ID> # only ONE conclusions
    weight :
      <Double between 0 and 1>

  # EXAMPLE:
  - arg1 :
    premise :
      - kill
      - intent
    exception :
    conclusion :
      murder
    weight :
      0.8
```

* `PROOFSTANDARD`
..* Begins with 'PROOFSTANDARD'
..* a sequence of map, each maps a `PROP_ID` to a `PROOFSTANDARD`
..* accepted `PS` are: `scintilla`, `preponderance`, `clear and convincing`, `beyond reasonable doubt`, and `dialectical validity`
```
PROOFSTANDARD :
  - <PROP_ID> : <PS>

  # Example
  - intent : beyond reasonable doubt
```

* `PARAMETER`
..* Begins with 'PARAMETER'
..* A map with 3 maps
..* 3 compulsory fields: `alpha`, `beta`, `gamma`
```
PARAMETER :
  alpha : <Double between 0 and 1>
  beta : <Double between 0 and 1>
  gamma : <Double between 0 and 1>
```

### Template
The template can also be found in [system/samples/template.yml](samples/template.yml)
```

```

## Tests
