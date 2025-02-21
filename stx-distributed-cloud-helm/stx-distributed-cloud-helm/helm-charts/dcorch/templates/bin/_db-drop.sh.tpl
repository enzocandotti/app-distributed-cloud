#!/bin/bash

{{/*
#
# SPDX-License-Identifier: Apache-2.0
#
*/}}

set -ex

if ! update-ca-certificates --localcertsdir /etc/pki/ca-trust/source/anchors; then
    echo "Failed to update CA certificates!" >&2
    exit 1
fi

dropdb -h 127.0.0.1 -Uroot dcorch
