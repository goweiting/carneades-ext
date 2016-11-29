# A dialogue view of argumentation

## Different types of dialogue:
- Deliberation - Solve a problem
- Persuassion - To test whether a claim is acceptable

**We only focus on `Persuassion` dialogues in Carneades**

## Parties arguing about some conclusion
- Proponent aims to establish some `Conclusion`
- Opponent aims to defeat the `Conclusion`

## What about dialogue?
Taken from the Gordon et al. 2007 paper:
1. *context can tell us whether some party has questioned or conceded a statement or whether a third-party (e.g. judge) has decided to accept or reject a claim taking into consideration the arguments which have been made*

2. *Information about the burden of proof allocated to the party who has the better access to evidence*

3. *Proof standard depends on the phase of the dialogue*

4. Carneades supports dialogue
  - In evaluation of arguments, it depends on:
      - whether statements have been questioned or decided
      - Allocation of burden of proof
      - Proof standard applicable to questioned statements
  - Which are in terms dependent on the stage and context of the dialogue


## Argument:
1. Consists of:
    - Premise (aka known as ordinary premise in the literature)
    - Exceptions
    - Conclusion
    - All are propositions
2. Arguments are defeasible

## Translating Argumentation Schemes into Carneades
Expresses reasoning policies dependednt on the norms of the community
- Argumentation schemes comes with a set of critical questions
- Critical questions enumerate ways of chaallenging arguments created using the scheme.
- Critical questions differ in impact on BOP - i.e. some CQ can shift the BOP to other party, some CQ causes the Burden of answering to be given to the party who raised the CQ; difference between CQs on how strongly or weakly they produce a shift
- **Each CQ can be modelled as `assumptions` an `exceptions` in Carneades**. Hence, its usage can use to model where the BOP lies

### How are BOP shifted when CQs are asked:
1. Theory 1 - Shifting burden Theory
> When the Question is asked the BOP automatically shifts to the other party to provide an answer; if she fails to do so, the argument defaults automatically
> Hence if an appropriate answer is given, then the original argument is restored

2. Theory 2 - Backup evidence theory
> Asking a CQ should not be enough to make the original argument default
> Thq question, if asked, needs to be backed up with some evidence before it can shift any burden back to the proponent

### Burden of Production
- CQ affects Burden of Production in particular
- Distribution of Burden of Production can be expressed by formulating Exceptions and Assumptions
- Whether an assumption or exception is appropriate depends on who should have the burden of Production
- if the respondent, the person raising the CQ, should have the BOProd, then CQ should be modeled as an Exception
- if the proponent should have the BOProd, then CQ modeled as an Assumption
- Which type of premise is appropriate depends on the policy for the argumentation scheme; hence new argumenttion schemes can be created.
> e.g. in the scheme for `arguments from expert opinion`, we can use the shifting burden theory to model expertise and backup evidence questions - hence using them as assumptions. Similarly, using exceptions to model the trustworthiness and consistency questions. Thus, for instance, if the respondent wants to challenge the trustworthiness of the expert, she will have to prove the exception is true.

### Burden of Persuassion
- Distribution of Burden of Persuassion CANNOT be expressed due to:
  - Exception has to be proven
  - Exception mereley has to be made plausible

### Carneades and Burden of Proof
- BOP is distributed by dividing premises into different types - Ordinary premises, assumptions and Exceptions
- initially low PS needs to be assigned to the statement of each premise
- after burden of production has been, the burden of persuassion can be distributed by rasigin the proof standard assigned to the statement
- changing the PS can also cause the burden to shift from one party to another

In general:
- Initial allocation of burden of production is regulated by the premise types of the argumentation scheme applied
- Burden of persuassion is allocated by assigning the appropriate PS
- As dialogue progresses, burdens may be reallocated by changing the assignment of premise types and proof standards via speech acts (speech acts can be modeled as functions which map a state of the dialogue to another)
