#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

mkdir -p /etc/yunohost/hooks.d/post_domain_add
install -m 755 "$pkg_dir/sources/hooks/60-wappos-cross-domain" /etc/yunohost/hooks.d/post_domain_add/60-wappos-cross-domain
