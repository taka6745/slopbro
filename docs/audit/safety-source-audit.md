# SlopBro and Homebrew Channel source safety audit

Target: LG OLED55C5PSA.AAUQLJD, firmware 43.21.77, webOS 26 / 11.2.0-3706.
Date: 26 October 2026 (Australia/Brisbane).

No TV calls or installer execution were performed for this audit. The follow-up
implementation runs only local refusal-path tests with mocked TV commands and
temporary fixtures. No code is committed or pushed by this reviewer.

## Scope and conclusion

- SlopBro upstream commit `21023d56ca424607bb03d2939609cc658c655fc7`.
- Homebrew Channel v0.7.3 source `92fcf9fef7ce08dbeae3b0616df8d0c75c11f0b3`.
- The fetched v0.8.0-rc1 tag diff, including permission, activity lifecycle,
  and UID-check changes.

The reviewed execution path contains no direct kernel, rootfs, bootloader,
raw-storage, or firmware-partition flashing. It does change persistent TV data,
application installation state, and Homebrew Channel service permissions. That
does not establish zero bricking risk, nor prove recovery from proprietary
service failures, storage failure, or interrupted changes.

The downloaded release artifact digest and source-to-package checks were
performed separately by the parent agent; this report's original findings are
source-level findings. No reproducible build equivalence or native binary audit
is claimed here.

## Findings against upstream

### P2: Unverified package before persistent changes

In `wwwroot/autoroot.sh`, upstream lines 115–128 use `curl -L` without HTTP-error
failure, bounded transfer time, or digest validation. Lines 421–430 also accept
an existing adjacent `hbchannel.ipk`. `perform_root` changes the developer-mode
marker before trying installation (255–263). A 404 body or incorrect package can
therefore leave a partly modified installation state if installation fails.

[Pinned upstream source](https://github.com/throwaway96/slopbro/blob/21023d56ca424607bb03d2939609cc658c655fc7/wwwroot/autoroot.sh#L115)

### P2: Conflicting Developer Mode state is checked too late

Upstream lines 168–183 replace an existing marker file with a directory. The
Developer Mode application is only checked at 314, after installation/elevation.
An unknown app-state result still exposes the reboot button (336–339).
`getAppInfo` returning false cannot safely distinguish absence from every service
error. A fresh-install preflight must require positively recognized app-list
structure, not infer absence from an error.

[Marker handling](https://github.com/throwaway96/slopbro/blob/21023d56ca424607bb03d2939609cc658c655fc7/wwwroot/autoroot.sh#L168)
[Late app check](https://github.com/throwaway96/slopbro/blob/21023d56ca424607bb03d2939609cc658c655fc7/wwwroot/autoroot.sh#L314)

### P2: No transactional installation or restoration journal

Upstream lines 255–281 perform marker change, app-installer restart, package
installation, and service elevation sequentially. Failure exits do not restore
the old state; the EXIT trap only removes a lock (71–90). The optional rename of
`start-devmode.sh` to `.backup` at 296 can replace an existing backup.

Homebrew Channel writes its app-specific service, role and manifest files in
place: v0.7.3 `services/elevate-service.ts` lines 59, 158, 258–274, and 304.
Partial writes can leave incomplete HBC configuration. It is not established
that this would brick the TV, but interrupted-state behavior is not proven safe.

[Installer sequence](https://github.com/throwaway96/slopbro/blob/21023d56ca424607bb03d2939609cc658c655fc7/wwwroot/autoroot.sh#L253)
[HBC elevation](https://github.com/webosbrew/webos-homebrew-channel/blob/v0.7.3/services/elevate-service.ts)

### P2: Completion messages do not verify root or persistence

The host waits for file requests only (`slopbro.py:1127–1129`). Files are marked
served before their response body transfers (`767–768`); HEAD requests also
reach the marker. The page reports service-launch acceptance, not installer
completion (`wwwroot/index.html:243–261`). `main.js:33–43` catches installer
errors and logs them without returning a terminal host success/failure signal.

[Host completion](https://github.com/throwaway96/slopbro/blob/21023d56ca424607bb03d2939609cc658c655fc7/slopbro.py#L1127)
[Installer invocation](https://github.com/throwaway96/slopbro/blob/21023d56ca424607bb03d2939609cc658c655fc7/wwwroot/main.js#L33)

### P2: Successful elevation exit can mean no usable service was found

HBC `elevate-service.ts:246–254` skips missing service definitions; missing
`run-js-service` returns false at 41–43. When no config changes, lines 321–323
exit normally. SlopBro treats a zero exit code as successful elevation.
Verification must execute a bounded read-only command through HBC and confirm
UID zero; a process exit status is insufficient.

## Persistent effects and recovery limitations

- The exploit downloads code into `/media/internal/downloads` before our guard
  library can execute. A guarded attempt is still a persistent TV mutation.
- SlopBro creates `/var/luna/preferences/devmode_enabled`, installs HBC in
  developer app storage, elevates its service, and may rename an old developer
  startup script. It offers a reboot dialog; the reviewed path does not force
  reboot directly.
- First opening HBC invokes `autostart` from
  `frontend/views/BrowserPanel.js:133`. `services/service.ts:799–833` copies the
  startup script into `/var/lib/webosbrew` and registers persistent activity.
- `services/startup.sh:72–75` starts unauthenticated root Telnet unless disabled;
  SSH is separately enabled. Lines 83–119 bind-mount temporary password and
  telemetry paths. This is a distinct operation from just installing HBC.
- Failsafe (`startup.sh:28–45`) depends on the TV booting far enough to run HBC,
  the files remaining readable, and networking working. It is not a bootloader
  recovery mechanism. The marker is cleared after ordinary startup (138–141).

[HBC startup](https://github.com/webosbrew/webos-homebrew-channel/blob/v0.7.3/services/startup.sh)
[HBC frontend autostart](https://github.com/webosbrew/webos-homebrew-channel/blob/v0.7.3/frontend/views/BrowserPanel.js#L133)

## Deliberate rc1 review

The original SlopBro package pin is 0.7.3. The parent audit found a C5 / 43.21.77
compatibility report requiring newer HBC and directed a deliberate rc1 change.

- rc1 adds `lunabus.query` API permissions and references the new permission
  file from the HBC manifest. This is an HBC-specific ACG compatibility change,
  not a system-partition modification.
- Activity lifecycle handling changes materially: a replacement activity
  manager avoids adopting/removing a persistent activity, uses an explicit
  persistent boot activity, and pauses callbacks on older webOS. The code is
  consistent with the stated persistence fix, but this is not hardware proof.
- The UID check changes from `process.uid` to `process.getuid()` in execbus.
- `startup.sh`, `jumpstart.sh`, and `run-js-service` have no tag-to-tag changes.
- No new direct firmware/bootloader write was found in the reviewed rc1 diff.
- No new critical issue was established in those changes; activity-manager
  behavior on the exact C5 still requires actual validation after installation.

[WebOS 11 fix PR 233](https://github.com/webosbrew/webos-homebrew-channel/pull/233)
[Maintainer rc1](https://github.com/throwaway96/webos-homebrew-channel/releases/tag/v0.8.0-rc1)
[C5 report](https://github.com/throwaway96/slopbro/issues/27)
[Direct rc1 report](https://github.com/throwaway96/slopbro/issues/45)

The candidate pins `org.webosbrew.hbchannel_0.8.0_all.ipk`, SHA256
`17c90447563c3f079e991d4276f52b058fc5288877b6e2cd14f48a2afd902a91`.
There is no automatic fallback or `latest` lookup.

## Implemented candidate and local validation

Branch: `slopbro/codex/preinstall-guards` (local branch name is
`codex/preinstall-guards`). Changes: root prerequisite, refusal of any existing
marker/symlink, strict successful nonempty listApps shape, refusal of Developer
Mode or existing HBC, package digest verification before marker creation,
HTTP-error handling and bounded package download, and explicit unverified
transfer-completion wording. The new guard is included in payload assets.

The parser uses the existing Node runtime. It has not observed this exact TV's
privileged listApps response and must fail closed if the shape differs.
No invented disk-space threshold or automatic rollback was added: those need
target-aware evidence rather than an arbitrary safety claim.

Independent review added refusal of abandoned startup scripts/backups and
`/var/lib/webosbrew` state, guard inclusion in the single-file packager, and an
OK-only completion notice with no reboot action or premature success claim.

Local validation: the 30-test suite passes with one packaging test explicitly
skipped under the default older interpreter; that artifact regression passes
separately under Python 3.13. This covers refusal cases and both file/embedded
payload inclusion. Tests source only the side-effect-free guard library, replace the TV
command with a local fixture executable, mock identity, and use temporary local
files. The installer main and all absolute TV mutation paths are excluded.

Shell syntax checks and `git diff --check` also pass. These results establish
guard behavior on the host, not rooting compatibility or zero bricking risk.

See `slopbro/SAFETY-REVIEW.md` for the candidate's concise usage limitations.
