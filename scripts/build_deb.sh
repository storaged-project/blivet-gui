#!/bin/bash
# Build a Debian package (.deb) for blivet-gui using a podman container.
#
# Usage: scripts/build_deb.sh [--distro DISTRO] [--release RELEASE]
#
# Options:
#   --distro   Base distribution: "debian" or "ubuntu" (default: ubuntu)
#   --release  Distribution release codename (default: noble for ubuntu, bookworm for debian)
#
# The built .deb files are placed in the deb-build/ directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

DISTRO="ubuntu"
RELEASE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --distro)
            DISTRO="$2"
            shift 2
            ;;
        --release)
            RELEASE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--distro DISTRO] [--release RELEASE]"
            echo ""
            echo "Options:"
            echo "  --distro   Base distribution: debian or ubuntu (default: ubuntu)"
            echo "  --release  Distribution release codename (default: noble for ubuntu, bookworm for debian)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

if [[ -z "$RELEASE" ]]; then
    case "$DISTRO" in
        ubuntu) RELEASE="noble" ;;
        debian) RELEASE="bookworm" ;;
        *)
            echo "Error: unsupported distro '$DISTRO', use 'debian' or 'ubuntu'" >&2
            exit 1
            ;;
    esac
fi

IMAGE="${DISTRO}:${RELEASE}"
CONTAINER_NAME="blivet-gui-deb-build-$$"

SPECFILE="$TOP_DIR/blivet-gui.spec"
VERSION=$(awk '/Version:/ { print $2 }' "$SPECFILE")
APPNAME="blivet-gui"

echo "=== Building ${APPNAME} ${VERSION} DEB package ==="
echo "    Distribution: ${DISTRO} ${RELEASE}"
echo ""

# -- Step 1: Create source tarball ----------------------------------------
echo "--- Creating source tarball ---"
make -C "$TOP_DIR" local

# python sdist normalizes the name (blivet-gui -> blivet_gui)
SDIST_NAME="blivet_gui-${VERSION}"
SDIST_TARBALL="${TOP_DIR}/${SDIST_NAME}.tar.gz"
if [[ ! -f "$SDIST_TARBALL" ]]; then
    echo "Error: tarball not created at $SDIST_TARBALL" >&2
    exit 1
fi

# -- Step 2: Prepare build context ----------------------------------------
BUILD_DIR="${TOP_DIR}/deb-build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Extract source tarball and rename directory to match Debian source package name
tar xzf "$SDIST_TARBALL" -C "$BUILD_DIR"
mv "${BUILD_DIR}/${SDIST_NAME}" "${BUILD_DIR}/${APPNAME}-${VERSION}"

# Copy debian packaging files into the extracted source
cp -a "$TOP_DIR/debian" "${BUILD_DIR}/${APPNAME}-${VERSION}/"

# Generate debian/changelog from the current version
cat > "${BUILD_DIR}/${APPNAME}-${VERSION}/debian/changelog" <<CHANGELOG_EOF
${APPNAME} (${VERSION}-1) UNRELEASED; urgency=medium

  * Upstream release ${VERSION}

 -- $(git -C "$TOP_DIR" config user.name) <$(git -C "$TOP_DIR" config user.email)>  $(date -R)
CHANGELOG_EOF

# Create the orig tarball that dpkg-buildpackage expects
cp "$SDIST_TARBALL" "${BUILD_DIR}/${APPNAME}_${VERSION}.orig.tar.gz"

# Clean up the source tarball from the project root
rm -f "$SDIST_TARBALL"

# -- Step 3: Build in container -------------------------------------------
echo "--- Building in ${IMAGE} container ---"

podman run --rm --name "$CONTAINER_NAME" \
    -v "${BUILD_DIR}:/build:Z" \
    "$IMAGE" \
    bash -exc '
        apt-get update
        apt-get install -y --no-install-recommends \
            build-essential \
            debhelper \
            dh-python \
            python3-all-dev \
            python3-setuptools \
            gettext \
            fakeroot \
            devscripts

        cd /build/'"${APPNAME}-${VERSION}"'
        dpkg-buildpackage -us -uc -b
    '

# -- Step 4: Report results -----------------------------------------------
echo ""
echo "=== Build complete ==="
echo "Output files in ${BUILD_DIR}/:"
ls -1 "${BUILD_DIR}"/*.deb 2>/dev/null || echo "(no .deb files found -- build may have failed)"
