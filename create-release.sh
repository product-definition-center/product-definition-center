#!/bin/bash
# Creates new package release in git.

set -e
set -o pipefail

fail() {
    echo "Error: $*" 1>&2
    exit 1
}

if ! git diff --quiet; then
    fail 'Make sure you have no uncommitted changes in your repository.'
fi

current_branch=$(git rev-parse --abbrev-ref HEAD)
if [[ "$current_branch" != "release" ]]; then
    fail 'Current git branch should be "release".'
fi

echo "Current git commit is: $(git describe)"

read -p 'Enter new version (e.g. "1.8.0"): ' version
if [[ ! "$version" =~ ^[1-9][0-9]*\.[0-9]+\.[0-9]+$ ]]; then
    fail 'Unexpected version format.'
fi

read -p 'Enter new release number: ' release
if [[ ! "$release" =~ ^[1-9][0-9]*$ ]]; then
    fail 'Unexpected release format.'
fi

sed -i 's/\(^Version:\s*\).*/\1'"$version"'/' pdc.spec
sed -i 's/\(^Release:\s*\).*/\1'"$release"'%{?dist}/' pdc.spec
sed -i 's/\(^VERSION = \)".*/VERSION = "'"$version"'"/' pdc/__init__.py

git add pdc/__init__.py
tito tag --keep-version

