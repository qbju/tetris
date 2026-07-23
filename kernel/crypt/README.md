# kernel/crypt

Pure-LPython cryptographic services for extensions. The public API uses a 3,840-byte isolated input/output buffer; the remaining space is internal scratch memory.

Implemented:

- `crypto.encoding`: RFC 4648 Base64.
- `crypto.hash`: SHA-256. Empty-input and `abc` known-answer tests run at boot.
- `crypto.symmetric`: AES-128-CTR. AES-128 FIPS 197 known-answer test runs at boot. CTR counter/nonce values must never be reused with the same key.
- `crypto.random`: SHA-256 counter DRBG. It starts unseeded and requires at least 16 caller-supplied seed bytes. This OS currently has no hardware entropy source, so callers must provide entropy from outside the VM; do not treat PIT/timing noise as cryptographically secure.

Reserved, not implemented: `crypto.pqc` (ML-KEM) and `crypto.legacy` (MD5). No primitive has received an external security audit.

Extensions must declare the corresponding `# permissions: crypto.*` entry. Each API returns `-1` for missing permission, `-2` for invalid buffer ranges, `-8` for an unseeded DRBG, and `-9` if the relevant boot self-test did not pass.