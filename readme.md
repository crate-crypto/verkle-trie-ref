## WIP


## Terminology

- commitment_to_field: This is converting a commitment to a scalar. Rename this to "commitment_to_scalar" to emphasise the fact that it is not the base field. (Even though the base field is not exposed)

- Hash of a node: node_commitment.commitment_to_field(). The fact that it does commitment_to_field is an implementation detail. It could do sha256 of all elements.
  
- Commitment to a node: commitment(node); Rename to node_commitment. Note, the fact that we use group elements could probably be abstracted. We only care about the fact that its a commitment to a node.
- 
- trie root: commitment(trie.root_node); We define the trie root as the commitment to the root node. We could define it as the node hash, there is no particular safety reason to choose either.

### Run tests

Example: `python -m verkle.verkle_test`

### Cryptography Modules

(In order of what you should implement first)

- ECC : contains all of the Elliptic curve arithmetic needed

- Polynomial : contains all of the polynomial arithmetic needed for polynomials in lagrange basis

- CRS : contains the common reference string which will be used to create proofs

- IPA : Proof algorithm that allows you to create an opening proof for one polynomial in lagrange form

- Multiproof : Proof algorithm that allows you to reduce an opening proof for multiple polynomials into an opening proof for one polynomial. We then call IPA to create a proof of the one _reduced_ polynomial.


