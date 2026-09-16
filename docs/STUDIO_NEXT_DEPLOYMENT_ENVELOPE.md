# Studio Next deployment envelope

This record captures the R11B deployment-forensics result for the COMMIT
reviewer-hardening candidate. It is a deployment control document, not proof
that a replacement deployment has already been submitted.

## Target identity

- Network: **GenLayer Studio Next**
- RPC: `https://studio-next.genlayer.com/api`
- Chain ID: `61997` / `0xf22d`
- Candidate branch: `fix/final-reviewer-blockers-r1`
- Candidate commit at investigation start: `47f793d0f79c97297dbed592137c9f2edfdffa35`
- Coordinator source SHA-256: `e235731ac223ee136b06b8cfc332065927a03553a3b1f5531571cd4d5da119c6`
- Helper source SHA-256: `dfb564fbd644fae756808fee2afc1f43c35d0dde095e33ad9f4802569e80007a`

## Required invariant

The deployment caller must explicitly bind the same non-zero value in both
places:

```text
consensusMaxRotations = 3
fees.distribution.rotations = [3]
```

The fee deposit must be recalculated after that distribution is constructed.
The deployment preflight must fail closed if either value is missing, zero, or
different from the other.

## Proven failure

The finalized candidate deployment transaction was:

```text
0x8aeb48b50ba8a9f125cddf52acbf28a2dba66020d6522c58784b84079906e139
```

It deployed the exact candidate source to:

```text
0x597641c88a3644f2C8c5c0baD9F1072710a82E85
```

The transaction executed successfully and the deployed bytes match the
candidate source, but the finalized envelope recorded:

```text
config_rotation_rounds = 0
fees.distribution.rotations = [0]
```

The caller-side runner intended three rotations, but passed a frozen fee object
whose distribution still contained `[0]`. This is a deployment-envelope defect,
not a source-code mismatch or a validator-timeout diagnosis.

## Measured Studio Next fee values

Using the live Studio Next fee policy observed during R11B and the same
deployment execution budget:

```text
rotations [0] -> 153643200002588 wei
rotations [3] -> 614572800010352 wei
```

These values are measurements from that policy snapshot, not reusable constants.
The next preflight must query the live policy again and recompute the deposit.

## Certification gates for the replacement

Before considering the replacement usable, record and verify all of the
following from the actual transaction:

1. chain ID `61997` and Studio Next RPC;
2. outer consensus rotation budget `3`;
3. fee-distribution rotations `[3]`;
4. finalized status and `FINISHED_WITH_RETURN`;
5. exact deployed coordinator bytes and SHA-256;
6. exact constructor helper binding;
7. successful `protocol_info()` read from the returned checksum address;
8. fresh current-source COMMIT, ABORT, recovery, and direct-claim lifecycle
   evidence.

Until those gates pass, the older deployment remains historical evidence only.
