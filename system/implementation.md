<!-- Notes on implementation goes here -->

<!-- From the paper:
1) To explicitly model where the burden of proof lies at each step
2) and select automatically from the set of available arguments an appropriate argument to introduce
-->

additional class:
`stage` = `<arguments, status>` where the status is a mapping to the argument's status, i.e. `{claimed, questioned}`

Starting with the main issue on contention - e.g. `murder`,
- find the arguments that are `pro` and `con` the statement
-
