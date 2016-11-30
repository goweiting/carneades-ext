<!-- Notes on implementation goes here -->

<!-- From the paper:
1) To explicitly model where the burden of proof lies at each step
2) and select automatically from the set of available arguments an appropriate argument to introduce
-->
```
Proponent = 'Prosecution'
Opponent = 'Defendant'
arguments node all have status = `NONE`
```
---
IN THE OPENING STAGE:
Starting with the main issue on contention by the proponent - e.g. `murder`,
- hence the proposition p = `murder` is *set* to status_{p} = `claimed`
- **burden of claiming** is satisfied; the premise of the argument for the proposition is added to the assumption of the jury - assumed to be true

the opponent now have the burden of questioning:
- find if there are any `con` arguments (rebuttal) or any other attack to the argument (e.g. questioning of the premise or the exception)
- if exists, the dialogue moves into the next phase - `argumentation phase`, and *set* status_{p} = `questioned`
- else the proponent have won - silence implies consent
---

IN THE ARGUMENTATION STAGE:
```
party who put forth the argument have burden of production for the premises
the respondent have the burden of prouction for the exception
```
Iteration...
- 0 :
  - Since the opponent attacked the claim, she have the burden of production for the **exception** OR producing a con argument
  - find this, and set the status of that argument to be `claimed` (an argument that attacks the exception or the con argument)
  - check using CAES:
    - argset = current arguments
    - ps = Scintilla
    - assumption
    - weights
    - alpha beta gamma
