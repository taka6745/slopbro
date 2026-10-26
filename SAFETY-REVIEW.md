# C5 pre-install guards — not hardware-tested

This branch stages a reviewed candidate for an LG OLED55C5PSA running firmware
43.21.77 / webOS 11.2.0-3706. It is not evidence of successful execution on that
TV, and cannot guarantee that rooting will not impair or brick the device.

See the [full source, reports, forks, and artifact review](docs/audit/SAFETY-REVIEW.md)
for the supporting evidence and verification limits.

## Deliberate package change

Upstream SlopBro installs Homebrew Channel 0.7.3. This branch deliberately pins
the maintainer's 0.8.0-rc1 artifact instead, because the release includes the
webOS 11 incoming Luna request permission fix (Homebrew Channel PR 233):

- [Maintainer release](https://github.com/throwaway96/webos-homebrew-channel/releases/tag/v0.8.0-rc1)
- [webOS 11 permission fix](https://github.com/webosbrew/webos-homebrew-channel/pull/233)
- [C5 / firmware 43.21.77 report](https://github.com/throwaway96/slopbro/issues/27)
- [Direct rc1 installation and reboot report](https://github.com/throwaway96/slopbro/issues/45)
- Artifact: `org.webosbrew.hbchannel_0.8.0_all.ipk`
- SHA256: `17c90447563c3f079e991d4276f52b058fc5288877b6e2cd14f48a2afd902a91`

The release candidate also changes activity-based startup handling. The review
found no change to `startup.sh`, `jumpstart.sh`, or `run-js-service` between the
reviewed tags. Compatibility reports are useful evidence, not a recovery
guarantee. There is no automatic version fallback or download of `latest`.

## Changes

- Require root before installer setup.
- Refuse any existing developer-mode marker, including a directory or dangling
  symlink. Never replace or delete it automatically.
- Refuse pre-existing developer startup scripts/backups or `/var/lib/webosbrew`
  state, including dangling symlinks, rather than overwrite an abandoned setup.
- Before persistent changes, require a successful `listApps` response with
  `returnValue: true` and a nonempty `apps` array of objects with string `id`s;
  refuse an installed LG Developer Mode app or existing Homebrew Channel. Errors, unknown response shapes,
  and unavailable tools stop the installation. The query shape has not yet
  been verified on this TV; failure must be investigated, not bypassed.
- Verify the pinned package SHA256 before creating the developer-mode marker.
- Fail package downloads on HTTP errors; use 15-second connection and 120-second
  overall timeouts. TLS verification remains enabled by default.
- State explicitly that payload requests do not verify installation or root.
- Replace the installer completion dialog with an OK-only notice to keep the
  TV on for root/recovery verification. It offers no reboot action or claim of
  verified rooting success.

The guard library uses the TV's existing `node` runtime, `luna-send`, `id`, and
`sha256sum`; it adds no Python dependency on the TV. Host tests mock TV commands
and use temporary fixtures. They never source or execute the installer main.

## Remaining limits

The exploit, boot persistence, HBC startup behavior, and recovery design have
not been rewritten. There is no automatic rollback. Installation is still not
transactional, and storage failure, interruption, proprietary service behavior,
or incompatible firmware remain risks. The guard checks are a snapshot, not a
lock against other TV processes changing state.

These checks precede installation and preference/service changes. They do not
precede the exploit page downloading its payload into `/media/internal/downloads`;
that is already a persistent TV write. This is not a read-only TV probe.

HBC's recovery mode requires the TV to boot sufficiently far to run HBC code
and networking. It is not bootloader recovery. First opening HBC invokes its
startup logic; default Telnet exposure and recovery access require a separate
reviewed setup step. Root, normal TV operation, and persistence must each be
verified before claiming success. No reboot should be inferred safe from a
completed file transfer or a zero exit code.

## Local checks

From this checkout:

```sh
python3 -m unittest discover -s tests -v
sh -n wwwroot/preinstall-guards.sh
bash -n wwwroot/autoroot.sh
```

These checks do not run a rooting attempt or establish hardware safety.
The single-file package artifact regression requires Python 3.12 or newer;
on older Python it is explicitly skipped and must be run with a newer interpreter.
