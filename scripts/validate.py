#!/usr/bin/env python3
"""Checks peers.yaml against what kees2 actually understands.

kees2 silently ignores unknown IX keys in not_on and crashes the whole run on
a missing description/import/export, so both are caught here before merge.
Keep IX_KEYS in sync with kees2 vars/generic.yml ixp_map.
"""
import ipaddress
import re
import sys

import yaml

IX_KEYS = {"amsix", "frysix", "speedix", "interix", "interix_old", "nineix", "ensix"}
ROUTERS = {"rtr1.as202585.net", "ens2rtr01.as202585.net"}
REQUIRED = {"description", "import", "export"}
KNOWN = REQUIRED | {
    "not_on", "not_with", "only_with", "private_peerings", "only_on", "accept_roa_valid",
    "blackhole_accept", "blackhole_community", "type", "route_server", "irr_order",
    "ipv4_limit", "ipv6_limit", "gtsm", "multihop", "disable_multihop_source_map",
}
IRR = re.compile(r"^(ANY|AS\d+|([A-Z0-9-]+::)?(AS\d+:)?(RADB::)?AS-[A-Z0-9_-]+(:AS-[A-Z0-9_-]+)*)$", re.I)

errors = []
peers = yaml.safe_load(open(sys.argv[1] if len(sys.argv) > 1 else "peers.yaml"))
for name, e in peers.items():
    def err(msg):
        errors.append(f"{name}: {msg}")
    if not re.fullmatch(r"AS\d+", str(name)):
        err("key must look like AS<number>")
    if not isinstance(e, dict):
        err("entry must be a mapping"); continue
    for k in sorted(REQUIRED - e.keys()):
        err(f"missing {k} (kees2 aborts the whole run)")
    for k in sorted(e.keys() - KNOWN):
        err(f"unknown key {k}")
    for obj in str(e.get("import", "")).split():
        if not IRR.match(obj):
            err(f"import {obj!r} is not an aut-num or as-set")
    for k in e.get("not_on") or []:
        if k not in IX_KEYS:
            err(f"not_on {k!r} is not a kees2 IX key ({', '.join(sorted(IX_KEYS))})")
    for k in e.get("only_on") or []:
        if k not in ROUTERS:
            err(f"only_on {k!r} is not a router ({', '.join(sorted(ROUTERS))})")
    for k in ("not_with", "only_with", "private_peerings"):
        for ip in e.get(k) or []:
            try:
                ipaddress.ip_address(str(ip))
            except ValueError:
                err(f"{k} {ip!r} is not an IP address")
    if e.get("type", "peer") not in ("peer", "upstream", "downstream"):
        err(f"type {e['type']!r} must be peer, upstream or downstream")

print("\n".join(errors) or f"ok: {len(peers)} entries")
sys.exit(1 if errors else 0)
