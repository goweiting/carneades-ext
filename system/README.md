# Carneades Argument Evaluation System (CAES) in Python
Requirements for the second coursework for INFR09043 Artificial Intelligence Large Practical ([AILP](http://www.inf.ed.ac.uk/teaching/courses/ailp/)) 2016/17 are:

- [4.1](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#4) Implementing file-reading capability
- [4.2](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Devising a syntax
- [4.3](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Deserialisation
- [4.4](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Provide examples

You can preview this markdown file using this [tool](https://jbt.github.io/markdown-editor/), although not necessary.

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
In this extension, a user approach

The user will create a file to contain all the statements (propositions), arguments, proofstandard and parameters required for CAES. The extension for the file is `.yml`. It is recommended that the file is stored alongside the `src` folder, for instance in the `samples` folder.

A general workflow:

1. User creates file for arguments, e.g. `caes.yml`
2. Setup virual environment - `ailp_env`
3. Either:
  * Start the python interpreter and import `carneades` (see [running from the interpreter](#Interpreter)), or
  * Run from the command line (preferred method)
4. The file (in step 1) will go through lexical analysis to ensure [synatx](#syntax) rules are obeyed before parsing it for the Carneades Argument Evaluation System.

## Directory
The directory of the files is as such:
```
system
|   README.md
└───src
|   └───carneades
|       |   caes.py
|       |   tokenizer.py
|       |   parser.py
|       |   ...
|
└───samples (all the test examples are here!)
|   |
|   |
|      
|
└───dot
|   ( contains all the .dot files generated from write_to_graphviz() function)
|
└───graph
|   ( argumentation graph generated using python-igraph and cairo)
|
└───log
|   ( the logging information when the caes is run)
|
└───ailp_env
    ( files for the virual environment, assumed to be set up already by user)

```
## Setup

### Activating `ailp_env` virtual environment

The `ailp_env` is not included (assumed is done; commands are listed below for reference), but can be set up according to [this](#https://github.com/ewan-klein/carneades#installing-the-libraries-for-the-carneades-sample-code-on-your-own-computer). On DICE machine, the virtual environment can be created using the following command:
```$
$ pyvenv ailp_env
```

## Running CAES

Two modes of running caes is supported:
### 1) from the command line
You can run CAES to evaluate single or multiple files. Assuming your source files are in the `system/samples` folder, and you are in the `system` folder
```$
(ailp_env) $ cd src/carneades
# to run a single file:
(ailp_env) $ python caes.py '../../samples/example.yml'
# to run multiple files:
(ailp_env) $ python caes.py ''../../samples/example.yml' ''../../samples/example2.yml'
```

### 2) from the interpreter
```(python)
from the system folder:
(ailp_env) $ cd src/carneades
(ailp_env) $ python # to start the python interpreter
>>> import caes
>>> reader = caes.Reader(buffer_size=4096, indent_size=2) # more about these parameters later
>>> reader.load('../../samples/example.yml')
```


## Syntax for `.yml` files
The syntax for the files are inspired from YAML, hence the extension name. YAML is a user friendly markdown language which does not have too many hierachical elements (such as brackets). The syntax rules are strict, and will throw up any error if it is not well followed. Syntax for caes illustrates the essential elements required for each caes.

### General Syntax Rules:
1. Spaces and newlines are delimiters. Usage of tab will result in error as the program is sensitive to indents (unless your editor converts them to space automatically).
2. Indents are represented using spaces, The standard indent size is `2` (i.e. two spaces - '  '). Similar to python, indents determine the grouping of statements. If you prefer a different indent-size, if must be changed when the `Reader` class is called, such as : `$ reader = Reader(indent_size = 3)` when using the python interpreter. Unfortunately, parsing using the command line will use the default indent size of 2
3. Comment begins with `#`, similar to python
4. the components of the syntax are:
  * headers (PROPOSITION, ARGUMENT, PROOFSTANDARD, ASSUMPTION, ACCEPTABILITY, PARAMETER)
  * compulsory fields for header
  * `:` - is a mapping value used to indicate the 'belongs-to' membership of items before it and after
  * `-`  - only used when representing a negated proposition under certain headers
  * items :
    * a series of character, such as: 'is witness2 sufficient to proof intent?'
    * a list : starts with `[` and ends with `]`, using `,` to separate the items


### Syntax for CAES

The syntax for CAES uses a natural language approach to represent propositions (also known as statements) in other literature, and arguments. Hence, the identifier for proposition and argument can be a long setence.

A template of the syntax is attached at [system/samples/template.yml](samples/template.yml)

* `PROPOSITION`
  * Begin with 'PROPOSITION' header; each proposition is at indent level 1
  * A proposition is uniquely identified by an identifier - `PROP_ID`. The polarity for all proposition is assumed to be true.

```
PROPOSITION :
  <PROP_ID> : <TEXT> # note the indent before each proposition is defined
  <PROP_ID> : <TEXT>
  <PROP_ID> : <TEXT>

Example:
PROPOSITION:
  murder: accused committed murder
```

* `ASSUMPTION`
  * Begin with 'ASSUMPTION' header, and is a list of `PROP_ID` defined above
```
ASSUMPTION : [ <PROP_ID>, <PROP_ID> ]
ASSUMPTION : [] # no assumptions present in arguments

Example:
ASSUMPTION : [kill, witness1, witness2, unreliable2]
```

* `ARGUMENT`
  * Begins in with 'ARGUMENT' header; each argument consist of an `ARG_ID` at indent level 1; and fields at indent level 2
  *  `ARG_ID` as key. Each map consist of the following maps: `premise`, `exception`, `conclusions`, `weight`
```
ARGUMENT :
  <ARG_ID> : # indent level = 1
    premise :  [ <PROP_ID> ] # each field is at indent level = 2
    exception : [ <PROP_ID> ]
    conclusion: <PROP_ID>
    weight : <Double between 0 and 1>

  # EXAMPLE:
  - is there an intent to murder?:
    premise : [kill, intent]
    exception : [] # empty list to represent no indent
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



## Tests
