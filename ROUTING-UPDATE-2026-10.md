# Routing update: 2026-10-08

`lmm.best` and every subdomain now use the `proxy` outbound. Their DNS queries use `doh-cloudflare`, whose transport also uses `proxy`. The suffix has a domain boundary: names such as `notlmm.best` and `lmm.best.example` do not match.

This requested exception precedes the Direct/Global mode rules, app rules, advertising lists, and country rules. DNS interception and the existing invalid-address/ICMP rejection rules retain their priority. With no configured proxy node, the empty proxy selector stays blocked; it does not silently use a direct connection.

Specific foreign AI and social-service rules precede generic China rules. Broad developer and communication categories stay after China rules, so a domestic mirror is not proxied only because it belongs to a broad category. Named developer services keep their specific proxy rules. Chinese top-level domains use their ASCII IDNA labels, matching DNS wire names.

The direct bootstrap resolver, domestic DNS exceptions, default DNS profile, and TUN/eBPF ownership are unchanged. No IP-wide exception is added. User-owned full configurations and explicit overrides remain user-owned; this template cannot force traffic from apps excluded from the core to enter it.

## Validation

Run `python3 generate.py --check` and `python3 -m unittest discover -s tests -v`.

The new tests cover LMM root/subdomains, all three modes, TCP/UDP, lookalike-domain exclusions, DNS interception priority, conflicting country/category rules, IDNA names, and the no-node policy. Rule-set memberships in these tests are synthetic: they validate ordering, not live Android traffic or current SRS membership.
