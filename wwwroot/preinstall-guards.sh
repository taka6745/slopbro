#!/bin/sh
# Read-only checks. Sourcing this file performs no checks or mutations.
# The caller must stop on any nonzero result before installing anything.

require_root() {
    if [ "$(id -u)" != '0' ]; then
        echo '[!] Refusing installation: root privileges were not obtained' >&2
        return 1
    fi
}

require_absent_path() {
    # -L catches dangling symlinks too. Existing roots/devmode need separate review.
    if [ -e "$1" ] || [ -L "$1" ]; then
        echo "[!] Refusing installation: path already exists: $1" >&2
        return 1
    fi
}

require_no_devmode_app() {
    # A false getAppInfo result is ambiguous (missing app OR service error).
    # Require a successful, structurally valid complete listApps response.
    if ! app_list="$(luna-send -w 5000 -n 1 -f 'luna://com.webos.applicationManager/listApps' '{}')"; then
        echo '[!] Refusing installation: cannot query installed apps' >&2
        return 1
    fi
    printf '%s' "$app_list" | node -e '
        try {
            var data = JSON.parse(require("fs").readFileSync(0, "utf8"));
            if (!data || data.returnValue !== true || !Array.isArray(data.apps) || !data.apps.length ||
                !data.apps.every(function (app) {
                    return app && typeof app.id === "string" && app.id.length > 0;
                })) throw new Error("unrecognized listApps response");
            if (data.apps.some(function (app) { return app.id === "com.palmdts.devmode"; }))
                throw new Error("LG Developer Mode app is installed");
            if (data.apps.some(function (app) { return app.id === "org.webosbrew.hbchannel"; }))
                throw new Error("Homebrew Channel already exists; this is a fresh-install-only candidate");
        } catch (err) {
            console.error("[!] Refusing installation: " + err.message);
            process.exit(1);
        }
    '
}

require_ipk_hash() {
    if [ ! -f "$1" ] || [ -L "$1" ]; then
        echo '[!] Refusing installation: package is missing or is a symlink' >&2
        return 1
    fi
    if ! package_hash="$(sha256sum -- "$1")"; then
        echo '[!] Refusing installation: cannot verify package SHA256' >&2
        return 1
    fi
    if [ "${package_hash%% *}" != "$2" ]; then
        echo '[!] Refusing installation: package SHA256 does not match reviewed release' >&2
        return 1
    fi
}

preinstall_checks() {
    require_root || return 1
    require_absent_path "$1" || return 1
    require_no_devmode_app || return 1
    require_ipk_hash "$2" "$3" || return 1
    # Remaining explicit paths cover abandoned developer/root installations.
    # Their absence is required; nothing is renamed or removed automatically.
    shift 3
    for state_path in "$@"; do
        require_absent_path "$state_path" || return 1
    done
}
