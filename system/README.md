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
In this extension of CAES, a syntax is created for users to input proposition (also known as statement in other literature), argument. This syntax is inspired by [YAML](#https://en.wikipedia.org/wiki/YAML) for its human-readibility, where the use of natural language to represent the argument titles, for instance, is welcomed. Also, the syntax is scalable, such that fields (such as adding a field to represent the `propnent` or `defendant` in for arguments) can be added by the user without much changes to the the tokenizing and parsing stages of the language.

To infer the depth and nesting of maps (or dictionary in python terms) in the source code, a data structure `Node` is used to store the tokens that the parser recrusively extracts at each depth.

The diagram that is produced from the native` draw()` and `write_to_graphviz()` functions are also modified to illustrate the weights of the arguments. The degree of 'red' for the boxes representing arguments highlight their respective weight.

The preferred method to visualise the argumentation graph is to use Graphviz. This overcomes the issue of user not able to get `python-igraph` or `cairo` on their computer. In such cases, they should comment out the `draw()` function in the `Reader` class, and the import of `Graph, plot` in the `caes.py` file to prevent errors. The graphiz digraph can be interpreted using an [online viewer](#http://dreampuf.github.io/GraphvizOnline/) by copying the contents of the respective `.dot` file (found in the `dot` folder adjacent to `src`).


A general workflow:

The user will create a file to contain all the statements (propositions), arguments, proofstandard and parameters required for CAES. The extension for the file is `.yml`. It is recommended that the file is stored alongside the `src` folder, for instance in the `samples` folder.

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
|   ( argumentation graph generated using python-igraph and cairo,, stored as .pdf)
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
The syntax for the files are inspired from YAML, hence the extension name. YAML is a user friendly markdown language which does not have too many hierachical elements (such as brackets). The syntax rules are strict, and will throw up any error if it is not well followed. A template with all the essential element is available in the `samples` folder.

### General Syntax Rules:
1. Spaces and newlines are delimiters. Usage of tab will result in error. The program is sensitive to indents, similar to python.
2. Indents are represented using spaces, The standard indent size is `2` (i.e. two spaces - '  '). Similar to python, indents determine the grouping of statements. If you prefer a different indent-size, if must be changed when the `Reader` class is called, such as : `$ reader = Reader(indent_size = 3)` when using the python interpreter. Unfortunately, parsing using the command line will use the default indent size of 2
3. Comment begins with `#`, similar to python
4. The components of the syntax are:
  * Basic data structure:
    * String, a series of character, such as: `is witness2 sufficient to proof intent?`
    * List : starts with `[` and ends with `]`, using `,` to separate the items
    * Dictionary : to indicate membership
  * Essential headers for CAES: `PROPOSITION`, `ARGUMENT`, `PROOFSTANDARD`, `ASSUMPTION`, `ACCEPTABILITY`, `PARAMETER`
  * `:` - is a mapping value used to indicate the 'belongs-to' membership of items before and after it
  * `-`  - only used when representing a negated proposition under certain headers


### Syntax for CAES

The syntax for CAES uses a natural language approach to represent propositions (also known as statements) in other literature, and arguments. Hence, the identifier for proposition and argument can be a long setence.

A template of the syntax is attached at [system/samples/template.yml](samples/template.yml)

* `PROPOSITION`
  * Begin with `PROPOSITION` header; each proposition is at indent level 1
  * A proposition is uniquely identified by an identifier - `PROP_ID`. The polarity for all proposition is `True`. To switch the polarity of the proposition in the other Headers, `-` is used before the `PROP_ID`, e.g.  `-kill` is the negation of `kill`

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
  * Begin with `ASSUMPTION` header, and is a list of `PROP_ID` defined above
  * As above, `-` is used to represent the negation of the proposition.
  * If no assumption is given, usage of an empty list `ASSUMPTION : []` is necessary
```
ASSUMPTION : [ <PROP_ID>, <PROP_ID> ]

Example:
ASSUMPTION : [kill, witness1, witness2, unreliable2]
```

* `ARGUMENT`
  * Begins in with `ARGUMENT` header; each argument consist of an `ARG_ID` at indent level 1; and respective fields at indent level 2.
  *  the compulsory fields are: `premise`, `exception`, `conclusions`, `weight`
```
ARGUMENT :
  <ARG_ID> : # indent level = 1
    premise :  [ <PROP_ID> ] # each field is at indent level = 2
    exception : [ <PROP_ID> ]
    conclusion: <PROP_ID>
    weight : <Double between 0 and 1>

# Examples:
ARGUMENT:
  is there an intent to murder?:
    premise : [kill, intent]
    exception : [] # empty list to represent no indent
    conclusion : murder
    weight : 0.8

  is witness1 sufficient to proof intent?:
    premise: [witness1]
    exception : [unreliable1]
    conclusion : reliable1
    weight: 0.2
```

* `PROOFSTANDARD`
  * Begins with `PROOFSTANDARD` header
  * For `PROP_ID`(s) that do not uses `scintilla` (the default proof standard), the `PROP_ID` is mapped to a `PS`
  * The accepted `PS` are: `scintilla`, `preponderance`, `clear and convincing`, `beyond reasonable doubt`, and `dialectical validity`
  * More about each standard [here](#proof-standards)
```
PROOFSTANDARD :
  <PROP_ID> : <PS>
  <PROP_ID> : <PS>

PROOFSTANDARD : [] # use `scintilla` for all propositions

# Example
PROOFSTANDARD:
  intent : beyond reasonable doubt
```

* `PARAMETER`
  * Begins with `PARAMETER` header
  * 3 compulsory fields: `alpha`, `beta`, `gamma`
  * See [proof standard](#proof-standards)
```
PARAMETER :
  alpha : <Double between 0 and 1>
  beta : <Double between 0 and 1>
  gamma : <Double between 0 and 1>

# Example:
PARAMETER:
  alpha : 0.8
  beta : 0.2
  gamma : 0.3
```


* `ACCEPTABILITY`
  * Begins with the `ACCEPTABILITY` header
  * A list of proposition that CAES should evaluate

```
ACCEPTABILITY : [ <PROP_ID> ]

# Example:
ACCEPTABILITY : [murder, -murder]
```

## Tests


## Proof Standards
The proof standards increases in strength. The weakest being `scintilla`, and the strongest being `dialetical validity`. The strength of a standard is use to the number of constraints it uses to determine if an argument is applicable.

1. `Scintilla` of evidence
> For a proposition p to satisfy the scintilla of evidence there should be at least one applicable argument pro p in CAES

2. `Preponderance` of the evidence
> For a proposition p to satisfy preponderance, it must satisfy scintilla and the maximum weight of the applicable arguments prop p is greater than the maximum weight of the applicable arguments con p.

3. `Clear and convincing` evidence
> For proposition p to satisfy this standard, it must satisfy preponderance of the evidence, and 1) the weight difference should be larger than a given constant `beta`, 2) there should be an applicable argument prop p that is stronger than a given constant `alpha`

4. `Beyond reasonable doubt`
> It must satisfy clear and convince evidence, and the strongest argument con p needs to be *less* than a given constant `gamma`, hence no reasonable doubt.

5. `Dialectical validity `
> This requires at elast one applicable argument prop p and no applicable aarguments con p.
