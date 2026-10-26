# LG C5 rooting review — 26 October 2026

Target: LG OLED55C5PSA.AAUQLJD, firmware 43.21.77, webOS 26 / 11.2.0-3706.

## Decision

The evidence supports a carefully staged attempt, but does not establish zero
bricking risk or guaranteed recovery. The stock installer has avoidable failure
paths and selects a Homebrew Channel version with a known webOS 11 permissions
gap. A small [review fork](https://github.com/taka6745/slopbro/tree/codex/preinstall-guards)
has been prepared and independently reviewed; it is not hardware-validated.

No rooting payload has been sent to this TV. The only TV interaction so far was
network discovery, device-information queries, and a user-accepted pairing.

## Evidence

- [Reports audit](safety-reports-audit.md): 57 upstream issues and 49 comments.
  A C5 on the same firmware reports working with HBC 0.8.0-rc1. A G5 reports
  the same firmware and exact internal webOS build. No report matches every
  field of this Australian C5 configuration. No permanent-brick report was
  found in the inspected corpus; this is not a measured failure rate.
- [Forks audit](safety-forks-audit.md): 28 listed forks, two substantive changes,
  one comparison unavailable. Neither substantive fork has established safer
  operation on this target. Large changes to startup/recovery and automatic
  retry behavior were rejected.
- [Source audit](safety-source-audit.md): installation changes developer-mode
  preferences and HBC service configuration, not firmware partitions. Its
  recovery facility depends on the operating system and networking starting.

Upstream SlopBro was pinned to
`21023d56ca424607bb03d2939609cc658c655fc7` (v0.1.0).
HBC v0.7.3 source was reviewed at `92fcf9fef7ce08dbeae3b0616df8d0c75c11f0b3`;
the maintainer's v0.8.0-rc1 tag was then compared separately.

## Package selection and verification

[HBC PR233](https://github.com/webosbrew/webos-homebrew-channel/pull/233)
adds the permission group needed by webOS 11. It is included in
[v0.8.0-rc1](https://github.com/throwaway96/webos-homebrew-channel/releases/tag/v0.8.0-rc1).
[SlopBro issue 45](https://github.com/throwaway96/slopbro/issues/45) documents
supplying rc1 directly to the rooting installer and checking root after reboot
on a different model. This is stronger evidence than a success title alone.

Both release packages were downloaded over HTTPS and their bytes matched the
digests published by GitHub's release API:

| Artifact | SHA-256 |
| --- | --- |
| HBC 0.7.3 | `d10bf3c753551d7c72fb7a92b20fcd2317e502a220ac668ba8e76f6ea78b363c` |
| HBC 0.8.0-rc1 | `17c90447563c3f079e991d4276f52b058fc5288877b6e2cd14f48a2afd902a91` |

The package control archives contain metadata only, with no install/remove
scripts. Both packages' startup.sh, jumpstart.sh, and run-js-service exactly
match their source tags. Remaining native binaries have identical hashes across
these versions. This does not prove reproducible builds or audit every binary.
Local records: [package metadata](review-artifacts/packages.json) and
[source comparisons](review-artifacts/package-source-checks.json).

## Boundaries for a live attempt

1. Record the exact reviewed commit and package digest. Confirm the TV is not
   updating and has stable power. Do not use a downgrade or a service-menu hack.
2. Use the established webOS 11 voiceweb/jsserver path, without alternate exploit
   retries. The payload download itself writes files to TV storage; a later
   pre-install refusal is not a completely write-free probe.
3. Stop before installation if root, package integrity, installed-app state,
   or the developer-mode marker is unexpected. Do not auto-uninstall apps or
   overwrite an existing root setup.
4. Treat file transfer and service-launch acknowledgement as intermediate
   events. Neither proves installation or root success. On any error, preserve
   logs and inspect the current state; do not blindly retry or reboot.
5. Verify actual root execution and recovery access before the first deliberate
   reboot. Preserve the recovery route until authenticated SSH works. Opening
   HBC activates additional startup behavior and is a separate step.
6. Verify the TV interface, inputs, streaming apps, and root after reboot before
   considering Glasshouse. Its webOS 26 home replacement is a separate
   experimental change, with its own restore path and validation.

## Limits

The TV's proprietary installer, jsserver, service manager and exact runtime
state cannot be exhaustively validated offline. The script has no atomic
transaction or guaranteed rollback after partial installation. Factory reset
is not a proven universal recovery method. A local test suite and checksums
reduce specific avoidable errors; they cannot certify that this physical TV
will never be bricked.

## Candidate validation

The patch pins HBC 0.8.0-rc1, checks root and package SHA-256, rejects conflicting
apps and pre-existing developer/root state, fails on HTTP download errors, and
uses bounded package downloads. It removes the reboot action and premature
success claim. It preserves the upstream exploit and HBC startup/recovery code.

Three agents divided source review, report review, and fork comparison. Two
independently reviewed the resulting patch; their packaging, stale-state, and
premature-reboot findings were fixed and re-reviewed.

Validation: 29 tests passed under the default Python interpreter; the remaining
packaged-artifact regression passed separately on Python 3.13. Shell syntax and
diff checks passed. The tests use local fixtures and mocked TV commands. They do
not run the installer on the host or contact a TV. No live rooting attempt was
performed during this audit.
