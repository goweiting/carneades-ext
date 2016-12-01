<!-- based on the paper by gordon et al in 2011-->

<!-- TODO:change name of acceptability to `issue` in question instead -->
Some one should decides on the `Issue` - which is in this implementation called `acceptability` -


New definition of dialogue: `<O,A,C>`, st each stage is a squence of `state`s - defined as `<arguments, status>`. The `arguments` is a set of arguments and status is a function mapping literals to their dialetical status in the state - i.e. {`claimed`, `questioned`}, and of course `None`. `None` is essential to allow the acceptability checker (of the issue in contention) to find out what are the states relevant in the current state

New insights on `Audience`:
- audience are able to assess the acceptability of propositions
- in this case, a value-based approach is used, i.e. the weight of each argument shows the relative strength for a particular audience.


New insights on `AES`:
- `<state, audience, standard>`
- standard is a total mapping of arguments (in state) to their applicable proof standards in the dialogue
- proof standard is function mapping `<issue, state, audience>` to `True` or `False`
- 
