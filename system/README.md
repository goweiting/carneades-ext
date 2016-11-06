# Carneades Argument Evaluation System (CAES) in Python
Requirements for the second coursework for INFR09043 Artificial Intelligence Large Practical ([AILP](http://www.inf.ed.ac.uk/teaching/courses/ailp/)) 2016/17 are:

- [4.1](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#4) Implementing file-reading capability
- [4.2](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Devising a syntax
- [4.3](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Deserialisation
- [4.4](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Provide examples


## Getting around this file:
Sections for this documentation includes:
* [Directory of folders](#directory)
* [Setting up the `ailp_env` virtual environment](#environment)
* [Understanding the workflow](#workflow)
* [Syntax for `.yml` files](#syntax)
* [Instructions for testing the system](#demo)
* [Running regression test](#testing)

Overview
======
The user will create a file to contain all the statements (propositions), arguments, proofstandard and parameters required for CAES. The extension for the file is `.yml`. It is recommended that the file is stored alongside the `src` folder, for instance in the `samples` folder.

-------
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
-----------
Workflow
========
---
## Syntax for `.yml` files

---
## DEMO
