#!/bin/bash
set -e

# This script builds SRPMs or RPMs in a containerized environment
# Usage: build.sh <mode> <archive_file> <spec_file>
#   mode: 'srpm' or 'rpm'
#   archive_file: path to the source tarball (mounted)
#   spec_file: path to the spec file (mounted)

MODE="${1:-srpm}"
ARCHIVE_FILE="${2}"
SPEC_FILE="${3:-koji-habitude.spec}"

if [ -z "$ARCHIVE_FILE" ]; then
    echo "Error: Archive file not specified" >&2
    exit 1
fi

if [ ! -f "$ARCHIVE_FILE" ]; then
    echo "Error: Archive file not found: $ARCHIVE_FILE" >&2
    exit 1
fi

if [ ! -f "$SPEC_FILE" ]; then
    echo "Error: Spec file not found: $SPEC_FILE" >&2
    exit 1
fi

ARCHIVE_NAME=$(basename "$ARCHIVE_FILE")
ARCHIVE_DIR=$(dirname "$ARCHIVE_FILE")

# Extract version from archive name (koji-habitude-VERSION.tar.gz)
VERSION=$(echo "$ARCHIVE_NAME" | sed -n 's/koji-habitude-\(.*\)\.tar\.gz/\1/p')

if [ -z "$VERSION" ]; then
    echo "Error: Could not extract version from archive name: $ARCHIVE_NAME" >&2
    exit 1
fi

# Copy mounted files to build directory
# cp "$ARCHIVE_FILE" "/build/$ARCHIVE_NAME"
# cp "$SPEC_FILE" "/build/koji-habitude.spec"

# Install buildrequires
echo "Installing buildrequires..."
dnf builddep -y /build/koji-habitude.spec || {
    # Fallback: install buildrequires manually from spec
    echo "dnf builddep failed, installing buildrequires manually..."
    dnf install -y python3-devel python3-pip python3-setuptools python3-wheel
}

# Build based on mode
if [ "$MODE" = "srpm" ]; then
    echo "Building SRPM..."
    rpmbuild --define "_sourcedir /build" \
             --define "_srcrpmdir /output" \
             --define "_topdir /build/rpmbuild" \
             -bs /build/koji-habitude.spec
    echo "SRPM built successfully in /output"

elif [ "$MODE" = "rpm" ]; then
    echo "Building RPM..."
    # First build SRPM, then build RPM from it
    rpmbuild --define "_sourcedir /build" \
             --define "_srcrpmdir /build/rpmbuild/SRPMS" \
             --define "_rpmdir /output" \
             --define "_topdir /build/rpmbuild" \
             -bs /build/koji-habitude.spec
    rpmbuild --define "_topdir /build/rpmbuild" \
             --rebuild /build/rpmbuild/SRPMS/koji-habitude-${VERSION}-*.src.rpm
    echo "RPM built successfully in /output/noarch"

else
    echo "Error: Invalid mode '$MODE'. Must be 'srpm' or 'rpm'" >&2
    exit 1
fi

# The end.
