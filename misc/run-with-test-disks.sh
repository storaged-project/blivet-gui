#!/bin/bash
# Run blivet-gui from this source tree using fake SCSI disks instead of real
# storage. The disks are created with targetcli using the same configuration
# as the BlivetUtils test suite, blivet-gui is started only on these disks and
# when it exits the disks are removed again.
#
# Run this as a normal user -- targetcli is called through sudo. blivet-gui
# itself should not run as root, it talks to a root daemon through pkexec.

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGETCLI_CONFIG="$TOP_DIR/tests/blivetutils_tests/targetcli_config.json"

if [ ! -f "$TARGETCLI_CONFIG" ]; then
    echo "targetcli configuration file '$TARGETCLI_CONFIG' not found" >&2
    exit 1
fi

for cmd in targetcli udevadm; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Required command '$cmd' not found in \$PATH" >&2
        exit 1
    fi
done

# targetcli needs root privileges
if [ "$(id -u)" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

cleanup() {
    echo "Removing the testing disks..."
    $SUDO targetcli clearconfig confirm=True >/dev/null 2>&1 || true
    $SUDO rm -f /var/tmp/blivetgui_test_disk*
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "Creating the testing disks..."
if ! $SUDO targetcli restoreconfig "$TARGETCLI_CONFIG"; then
    echo "Failed to create the testing disks" >&2
    exit 1
fi
$SUDO udevadm settle

# Find the newly created disks -- they all use the "blivetgui_test_" model.
test_disks=()
for sysdev in /sys/block/sd*; do
    [ -r "$sysdev/device/model" ] || continue
    if [ "$(tr -d '[:space:]' < "$sysdev/device/model")" = "blivetgui_test_" ]; then
        test_disks+=("/dev/$(basename "$sysdev")")
    fi
done

if [ "${#test_disks[@]}" -eq 0 ]; then
    echo "No testing disks found, something went wrong" >&2
    exit 1
fi

echo "Starting blivet-gui on: ${test_disks[*]}"
echo "Close blivet-gui to remove the testing disks."

PYTHONPATH="$TOP_DIR" PATH="$TOP_DIR:$PATH" "$TOP_DIR/blivet-gui" "${test_disks[@]}"
