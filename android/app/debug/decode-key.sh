#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
base64 -d "$here/lasso-dev.p12.b64" > "$here/lasso-dev.p12"
