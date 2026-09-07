#!/usr/bin/env python3
# Auteur : Patrick Ritaine

import json
import subprocess

_SSO_CSP_HEADER = (
    "Content-Security-Policy: upgrade-insecure-requests; default-src 'self'; "
    "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
    "object-src 'none'; img-src 'self' data:;"
)

_SSO_REWRITES = f"""rewrite ^/yunohost/sso$ /wappos-portal/ redirect;
rewrite ^/yunohost/sso/(?!applogos/|css/|assets/|customassets/|fonts/)(.*)$ /wappos-portal/$1 redirect;

location ~ ^/yunohost/sso/applogos/(.*)$ {{
  access_by_lua_block {{
    return
  }}
  alias /usr/share/yunohost/applogos/$1;
  more_set_headers "{_SSO_CSP_HEADER}";
}}

location ~ ^/yunohost/sso/customassets/custom\\.css$ {{
  access_by_lua_block {{
    return
  }}
  alias /usr/share/yunohost/portal/customassets/$host.custom.css;
  etag off;
  expires off;
  more_set_headers "Cache-Control: no-store, no-cache, must-revalidate";
  more_set_headers "{_SSO_CSP_HEADER}";
}}

location ~ ^/yunohost/sso/(css|assets|fonts)/(.*)$ {{
  access_by_lua_block {{
    return
  }}
  alias /usr/share/yunohost/portal/$1/$2;
  more_set_headers "{_SSO_CSP_HEADER}";
}}
"""

_ROOT_REWRITE = "rewrite ^/$ /wappos-portal/ redirect;\n"

_HEADER_FILTER = """header_filter_by_lua_block {
  local loc = ngx.header["Location"]
  if loc then
    local new_loc = loc:gsub("/yunohost/sso", "/wappos-portal")
    if new_loc ~= loc then
      ngx.header["Location"] = new_loc
    end
  end

  local sc = ngx.header["Set-Cookie"]
  if sc then
    if type(sc) == "table" then
      for i, v in ipairs(sc) do
        sc[i] = v:gsub("^yunohost%.portal=", "wappos.portal=")
      end
      ngx.header["Set-Cookie"] = sc
    else
      local new_sc = sc:gsub("^yunohost%.portal=", "wappos.portal=")
      if new_sc ~= sc then
        ngx.header["Set-Cookie"] = new_sc
      end
    end
  end
}
"""

_COOKIE_REWRITE = """rewrite_by_lua_block {
  local cookie = ngx.var.http_cookie
  if cookie then
    local new_cookie = cookie:gsub("wappos%.portal=", "yunohost.portal=")
    if new_cookie ~= cookie then
      ngx.req.set_header("Cookie", new_cookie)
    end
  end
}
"""


def _yunohost_json(*args):
    out = subprocess.run(
        ["yunohost", *args, "--output-as", "json"],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def _domains_with_root_app():
    apps = _yunohost_json("app", "list").get("apps", [])
    result = set()
    for app in apps:
        domain_path = app.get("domain_path") or ""
        if "/" not in domain_path:
            continue
        idx = domain_path.index("/")
        domain, path = domain_path[:idx], domain_path[idx:]
        if path == "/":
            result.add(domain)
    return result


def write_fragment(domain: str, has_root_app: bool) -> None:
    conf_dir = f"/etc/nginx/conf.d/{domain}.d"
    subprocess.run(["mkdir", "-p", conf_dir], check=True)
    content = _COOKIE_REWRITE + _HEADER_FILTER + ("" if has_root_app else _ROOT_REWRITE) + _SSO_REWRITES
    with open(f"{conf_dir}/wappos_sso_bypass.conf", "w") as f:
        f.write(content)


def regenerate_all() -> None:
    domains = _yunohost_json("domain", "list").get("domains", [])
    root_app_domains = _domains_with_root_app()
    for domain in domains:
        write_fragment(domain, domain in root_app_domains)


if __name__ == "__main__":
    regenerate_all()
