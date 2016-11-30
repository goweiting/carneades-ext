<!-- This notes  is based on the 2009 paper on which the haskell implementation is based on. The model for burden of proof is excluded in the implementation-->

### Argumentation is a Dialogical process for making justified decisions
- Goal: clarify and decided the issues, and produce a justification of the decision which can withstand a critical evaluation by a particular audience
- Input: initial claim or issue
- output:
    1. a set of claims
    2. the decision to accept or reect each claim
    3. A theory of the generalisations of the domain and the facts of the particular causes
    4. Proof justifiying the decision of each issues, showing how the decision is supported by the theory == demonstrate to an audience that a proposition satisfies its applicable proof standard


## Definitions
### Arguments
- <P,E,c> - are all proposition literals - atomic proposition or negated atomic proposition
- c : if p is c then argument is PRO p; if p is complement of c then argument is CON p

### Dialogue
- `<O,A,C>` - are the Opening, Argumentation, Closing stage
- Each stage is a tuple `<arguments, status>`
- *arguments* is a set of arguments
- status is a function mapping conclusions of the arguments in *arguments* to their dialectical status in the stage
  - dialectical status are either : CLAIMED or QUESTIONED
- the arguments must be acyclic

### Audience
- `<assumptions, weight>`
- Assumptions a set of atomic propositions or the negations assumed to be **acceptable** by the audience
- weight is a partial function mapping arguments to real numbers- representing the relative weights assigned by the adueince to the arguments
- weights models the relative strength of arguments to the audience

### Argument Evaluation Structure (AES)
- `<stage, audience, standard>`
- stage is a stage in a dialogue
- audience is an audience
- standard is a total function apping propositions to their applicable proof standards in the dialogue

### Proof standards
- is a function mapping tuples of the form `<issue, stage, audience>` to either True or False
- Scintilla
- Preponderance (aka Best Argument)
- Clear and convincing argument
- Beyond reasonable doubt
- Dialectical validity

#### Acceptability
A literal p is acceptable in an argument evaluation structure <stage, audience, standard> iff standard(p, stage, audience) is true

#### Applicability
An argument `<P,E,c>` is applicable in this AES iff
- The argument is a member of the arguments of the stage
- Every proposition p in the **Premises** is an assumption of the audience OR
- if nethier p nor -p is in assumption, p is acceptable in the AES
- No proposition e in the **Exceptions** is an assumption of the audience OR
- if neither e nor -e is in assumption, e is NOT acceptable in the argument evaluation structure

---
## Different types of burden of proof:
### Burdens of claiming and questioning:
IN THE **OPENING** STAGE
```
let <arguments_{n}, status_{n}> be the last stage s_{n} of the **opening stage**.
then:
1. a party has met the *burden of claiming* a propoisition p iff status_{n}(p) is either CLAIMED or QUESTIONED
2. the *burden of questioning* a proposition p has been met iff status_{n}(p) = QUESTIONED
```

---
### Burden of production
IN THE **ARGUMENTATION** STAGE
- Proponent of an argument has the burden of production for its ordinary premises
- Respondent to the argument has the burden of production for any exceptions
```
let <arguments_{n}, status_{n}> be the last stage s_{n} of the **argumentation stage**. let AES <s_{n}, audience, standard> where standard maps every proposition to `Scintilla`
then:
The burden of production for a proposition p has been met iff p is acceptable in AES
```
---

### Burden of Persuassion
IN THE **CLOSING** STAGE
- is met iff at the end of the closing phase, the proposition at issue is acceptable to the audience
- In this stage, a specific proof standard is used. This ps depends on the argumentation protocol (e.g. beyond reasonable doubt in criminal proceedings; Preponderance in civil proceedings)
```
let <arguments_{n}, status_{n}> be the last stage s_{n} of the **argumentation stage**. let AES <s_{n}, audience, standard> where standard maps every proposition to `Scintilla`
then:
The burden of persuassion for a proposition p has been met iff p is acceptable in AES
```
