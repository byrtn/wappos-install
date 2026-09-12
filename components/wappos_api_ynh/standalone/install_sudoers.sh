#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

for suffix in du adguard domains_public ssh_access security_status; do
    sudoers_name="/etc/sudoers.d/${app}_${suffix}"
    sed "s/__APP__/$app/g" "$pkg_dir/standalone/conf/wappos_api_${suffix}.sudoers" > "$sudoers_name"
    chmod 440 "$sudoers_name"
    chown root:root "$sudoers_name"
    visudo -c -f "$sudoers_name"
done
