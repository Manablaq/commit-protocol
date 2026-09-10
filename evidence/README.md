# Studio Dev evidence fixtures

These JSON files are deterministic fixtures intended for public hosting for the live Studio Dev
mission recorded in [`../docs/DEPLOYMENT_LOG_STUDIO_DEV.md`](../docs/DEPLOYMENT_LOG_STUDIO_DEV.md).
They are deliberately bound to one mission, intent digest, effect root, and
expiry. The contract reads them through `raw.githubusercontent.com` and checks
the complete v2 envelope plus the canonical payload Keccak hash.

They demonstrate URL/path authority binding and schema validation. They do not
claim to represent independent real-world issuers or cryptographic signatures.
