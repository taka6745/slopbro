# SlopBro fork audit — 2026-10-26

Target: LG OLED55C5PSA.AAUQLJD, firmware 43.21.77, webOS 26 / 11.2.0-3706.

This was a read-only source and provenance review. No TV connection or payload execution occurred during this audit. Fork code was downloaded into `/tmp/lg-forks-audit/`; the working SlopBro repository was not modified.

## Coverage

Compared the default branches of all 28 forks returned by GitHub's API against upstream `21023d56ca424607bb03d2939609cc658c655fc7`:

- 17 identical.
- 7 behind by four commits.
- 1 ahead by an empty/no-content-change commit.
- 1 comparison unavailable (HTTP 404).
- 2 contain substantive changes: Code-Allergy and wakamex.

The machine-readable snapshot is [review-artifacts/forks-comparison.json](review-artifacts/forks-comparison.json). This covers the returned forks' default branches, not every non-default branch or private/deleted fork.

## Substantive forks and alternatives

| Source | Useful changes | Limitations |
| --- | --- | --- |
| [Code-Allergy `10c941c5`](https://github.com/Code-Allergy/slopbro/commit/10c941c5e6848a9c5171f8f43c8e76e898007968) | Pinned HBC package hash; preflight; structured installation status; current-root check; bounded operations; HTTPS and certificate constraints. | Explicitly never tested on a physical TV. Large installer/startup rewrite. Removes Telnet even in failsafe and initially disables SSH, changing recovery access. Partial rollback only. |
| [wakamex](https://github.com/wakamex/slopbro), head `093567f4059fddd3942e77cac1583b6dfb75dd1f` | Download validation, SHA-256, parser fixes, timeouts, source-IP checks, WebSocket improvements. | 49 added commits; no specific C5/43.21.77 hardware validation identified. Automatic alternate-directory retries expand behavior. Its terminal `ok` means launch acknowledgement, not verified installation or root. |
| [ihovsky/webos-root](https://github.com/ihovsky/webos-root) | Checks Voice Assistant and Developer Mode; waits for HBC and asks the user to confirm Root OK before reboot. | Revised wizard explicitly untested on a TV. Original test was OLED77G6RLA / 43.11.78. Automatically switches loaders after certain failures/timeouts. |
| [raws0kil/jsbro-autoroot](https://github.com/raws0kil/jsbro-autoroot) | Original jsserver approach, browser UI. | Uses `dangbei-overlay` rather than the webOS 11 `voiceweb` path. Automatically removes Developer Mode. No target-specific reason to prefer it. |

## Concrete caveats

1. **wakamex does not verify root in its status beacon.** `wwwroot/index.html:373–374` reports `ok` immediately after jsserver acknowledges service launch. This must not be labelled successful rooting.
2. **Code-Allergy changes recovery behavior.** `SECURITY.md:42–56` explicitly requires physical-TV validation, including boot persistence and power-loss recovery. Lines 63–67 document partial rollback and warn against blind retries/reboots. `wwwroot/autoroot.sh:99–108` replaces startup and disables remote access before package installation. Its network hardening is not automatically a reduction in recovery risk.
3. **Broad automatic retry is inappropriate for unexpected failures here.** wakamex `wwwroot/index.html:275–283` changes download directories and restarts downloads for broad permission/path errors. An unexpected target response should stop for inspection.

## Recommended minimal changes

Retain upstream exploit selection, arguments, and initial HBC startup behavior. Do not adopt either large fork wholesale or rewrite the exploit.

- Verify the official HBC release against an independently obtained SHA-256 before persistent changes. Reject HTTP failures, empty files and mismatches. Both substantive forks specify `d10bf3c753551d7c72fb7a92b20fcd2317e502a220ac668ba8e76f6ea78b363c`; this audit did not independently download/hash the release.
- Preflight the target app, Developer Mode state, existing HBC/custom startup, and required commands. Stop on unknown or previously modified state.
- Report transfer completion, launch acknowledgement, installation completion, current root and reboot persistence separately.
- Give explicit installation failure precedence over text containing `installed`. Unknown response forms should stop, not be guessed successful.
- Bound host waits and retain diagnostic logs without automatically retrying/rebooting. A timeout does not establish that the TV process stopped.
- Preserve a recovery route until key-authenticated SSH is proven. Do not transplant an untested replacement startup merely to disable every existing recovery mechanism.

Focused wakamex changes worth examining, not blindly cherry-picking:

- [Checksum verification, `adabbb8c`](https://github.com/wakamex/slopbro/commit/adabbb8cf3a4356813c5d0ca87a36d0d25b95914)
- [Explicit installation status matching, `32830b7d`](https://github.com/wakamex/slopbro/commit/32830b7d27acf1cbaa346d46cb17960f73887a26)
- [Nonfatal notifications and download-error handling, `8492b94e`](https://github.com/wakamex/slopbro/commit/8492b94eab9524549ef97219e85adbe5b423faaf)

## Conclusion

The forks offer useful guards, but no inspected fork establishes safer operation on this exact model/firmware. Small reviewed changes can reduce avoidable failure modes. Neither source review nor offline tests can prove zero bricking risk or guarantee recovery on this physical TV.
