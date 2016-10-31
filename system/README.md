# Carneades Argument Evaluation System (CAES) in Python
Requirements for the second coursework for INFR09043 Artificial Intelligence Large Practical ([AILP](http://www.inf.ed.ac.uk/teaching/courses/ailp/)) 2016/17 are:

- [4.1](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#4) Implementing file-reading capability
- [4.2](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Devising a syntax
- [4.3](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Deserialisation
- [4.4](www.inf.ed.ac.uk/teaching/courses/ailp/2016-17/assignments/assignment2.pdf#5) Provide examples


## Getting around this file:
Sections for this documentation includes:
* [Directory of folders](#directory)
* Setting up the [system](#setup)
* [Instructions for testing the system](#demo)


---

## Directory
The directory of the files is as such:
```
system (<< you are here)
|   README.md
└───src
|   |   README.md
|   |   LICENSE
|   |
|   └───carneades
|       |   __init__.py
|       |   caes.doctest.py
|       |   caes.py
|       |   tracecalls.py
|       |
|       └───examples
|           |   sherlock.py
|           |   library.py
|
└───ailp_env
    └───bin
        |   activate
        |   ... (omitting rest of bin folder)

```
## SETUP

### Activating the `ailp_env` first
Need to activate the `ailp_env` before running the code:
```$
[From the current folder]
$ source ailp_env/bin/activate
(ailp_env) $  # the environment name should appear on each line in terminal
```

### How to run
```$
(ailp_env) $ cd src/carneades
(ailp_env) $ python
(ailp_env) >>> import caes # import the evaluation system
```

---
## DEMO
