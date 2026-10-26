# SlopBro reports and Homebrew Channel version audit

Reviewed 2026-10-26. Target: LG OLED55C5PSA.AAUQLJD, firmware 43.21.77,
webOS 26 / 11.2.0-3706. This was read-only research; no TV commands were run.
No credentials or serial numbers are included.

## Conclusion

Public evidence supports plausible compatibility, not a guarantee against
bricking. The closest C5 report uses firmware 43.21.77 with Homebrew Channel
0.8.0-rc1. Stock SlopBro downloads 0.7.3, which lacks a relevant webOS 11
permission fix. Do not choose the stock package just because many issue titles
say "working". No exact full model/region/firmware match was found.

## Coverage and limits

Retrieved all 57 public upstream SlopBro issues, all 49 public issue comments,
and the release list through GitHub REST. Each collection was shorter than its
100-result page size, so no further pagination was required. Discussions are
disabled. Inspected relevant issue bodies and comments, not just titles. Exact
model web searches found LG firmware listings but no exact PSA rooting report.

No permanent-brick or bootloop report was found in this upstream corpus. This
is a bounded negative result, not a measured failure rate: reports are
self-selected, their verification quality varies, and there is no denominator.
Several reports use similar machine-generated wording; treat them as user
reports rather than independent technical validation.

## Compatibility evidence

| Report | Evidence | Limitation |
| --- | --- | --- |
| [#27, Oct 24 comment](https://github.com/throwaway96/slopbro/issues/27#issuecomment-6382247196) | OLED65C57LA.DEUQLJP, firmware 43.21.77, working with HBC 0.8 rc1. Closest C5/firmware match. | Different size/region; no commit, command, cold boot evidence, or exact internal build in comment. |
| [#27, original and Oct 19 comment](https://github.com/throwaway96/slopbro/issues/27#issuecomment-6271162398) | OLED55C57LA, firmware 43.21.73, webOS 26. Root status appeared OK, but author needed HBC 0.8 rc1 for actual functionality. | Does not identify the exact failing operation with 0.7.3. Root OK alone is insufficient validation. |
| [#41](https://github.com/throwaway96/slopbro/issues/41) | OLED77G54LW with exact firmware 43.21.77 and exact webOS 11.2.0-3706 reports success. | G5, not C5. Very short body; no HBC version, commit, logs, or reboot evidence. |
| [#43](https://github.com/throwaway96/slopbro/issues/43) | US G5 83-inch, firmware 43.21.77, webOS 11 option; Root OK after reboot and full power cycle. | Different hardware; no exact commit or HBC version. Cross-region patch-equivalence assertion is reporter inference. |
| [#37](https://github.com/throwaway96/slopbro/issues/37) | Title reports OLED55C5PUA / 33.31.69 / main working. | Body is only thanks; different firmware generation and weak verification. |
| [#45](https://github.com/throwaway96/slopbro/issues/45) | G4 43.21.73, webOS 11.2.0-3703, SlopBro 21023d5, HBC 0.8.0-rc1 supplied locally. Post-reboot root id and service checkRoot verified; TV operational. | Different model/firmware. Stronger verification and evidence of direct rc1 provision to the installer. |

## Failure and recovery evidence

- [#44](https://github.com/throwaway96/slopbro/issues/44): G6 firmware 43.21.79
  rejects the service path despite the workaround. A launch rejection, not a
  reported brick; does not prove all model families with that version are patched.
- [#6](https://github.com/throwaway96/slopbro/issues/6): C5 reports hanging while
  waiting for downloads; original reporter says Internet connection was lost.
  Some commenters resolved it by fixing firewall/network placement. No permanent
  damage stated.
- [#22](https://github.com/throwaway96/slopbro/issues/22): exact SlopBro 21023d5
  reports completion on UA85; after Developer Mode removal and reboot HBC is
  absent and root remains unverified. TV still responds. Completion toast is
  insufficient.
- [#32](https://github.com/throwaway96/slopbro/issues/32): CX previously rooted,
  then failed after factory reset because devmode_enabled remained immutable.
  Reporter cleared the attribute and succeeded. Factory reset is not necessarily
  a clean initial state. This does not justify blanket attribute changes.
- [#14](https://github.com/throwaway96/slopbro/issues/14): manual unroot and broad
  recursive sweeps encountered bind-mount loops, exhausting resources and
  temporarily locking the UI/remote. Persistence remnants survived. No maintained
  clean-unroot procedure established. The reporter's "foolproof" factory-reset
  claim is unverified and should not be treated as a recovery guarantee.
- [#20](https://github.com/throwaway96/slopbro/issues/20): request for a staged
  stop before installation did not produce a documented stop/resume contract.
- [#23](https://github.com/throwaway96/slopbro/issues/23), asking whether this can
  brick a TV, has no body or comments. It is not a bricking report.

## Version context

[SlopBro v0.1.0](https://github.com/throwaway96/slopbro/releases/tag/v0.1.0),
published September 28, resolves to
21023d56ca424607bb03d2939609cc658c655fc7, the original local checkout. It adds the
service-path patch workaround. Several September failures predate it and should
not be presented as failures of this exact revision. Current failures remain,
including #44 and #51, so it is not universally compatible.

## Homebrew Channel 0.8.0-rc1 follow-up

[PR 233](https://github.com/webosbrew/webos-homebrew-channel/pull/233), merged
August 3 at 50fa99e1f08959b665b2e34d0d85cb2222c4c2c9, is directly relevant to
webOS 11: unprivileged apps/services no longer receive the public access-control
group. The change adds lunabus.query access to elevated services. That provides
a concrete explanation for Root OK coexisting with failed HBC operations on
webOS 11. It is a compatibility fix, not a proof against bricking.

[PR 230](https://github.com/webosbrew/webos-homebrew-channel/pull/230), merged
August 3 at 1a2b969e992617c9ba4b8a891542cb93a9e07b0a, primarily fixes autostart
on old webOS: private-bus selection, activity pausing, activity-adoption behavior,
and replacement of previewMetadata. Its fake activity-manager behavior is used
unconditionally, so it is not exclusively old-platform code, but it should not
be described as the webOS 11 permissions fix.

The [rc1 release](https://github.com/throwaway96/webos-homebrew-channel/releases/tag/v0.8.0-rc1)
was published September 24 and points at 7312e51. The release page itself has
only a changelog link, without a separate safety or installation rationale.
The [tagged changelog](https://github.com/throwaway96/webos-homebrew-channel/blob/v0.8.0-rc1/CHANGELOG.md)
lists PRs 230 and 233, Luna error handling (222), user-ID checking (231), and
removal of unused utilities (221). Tagged elevate-service source includes
lunabus.query; tagged fake-activity-manager.ts is present. These observations
verify that the release source includes the relevant fixes; they do not prove
that a downloaded binary was reproducibly built from that source.

### Direct first installation versus update

[SlopBro #45](https://github.com/throwaway96/slopbro/issues/45) explicitly says
rc1 was supplied locally as wwwroot/hbchannel.ipk during the rooting process,
then verifies root after reboot. This supports direct provision of rc1 to the
installer, rather than requiring a stock-0.7.3-then-update sequence. However,
the report does not explicitly document a factory-clean TV or exclude all prior
HBC installation history. Treat it as direct-install-method evidence, not a
controlled clean-first-install trial on the user's C5.

#27's initial C5 report describes needing to install rc1 after Root OK, so that
one supports an update path. Its same-firmware C5 follow-up does not specify
installation sequence. Neither establishes that the two-step path is necessary.

Recommendation: if proceeding, prefer a reviewed, pinned package appropriate
for webOS 11 and validate actual privileged operation and reboot persistence.
Avoid an unnecessary intermediate HBC version and an extra update operation
solely because the stock installer uses it. Keep the exploit mechanism unchanged
unless a concrete defect requires changes. No report review can establish zero
bricking risk or a guaranteed remote recovery route.
