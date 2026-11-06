# MagicSingBox
MagicNet x sing-box

## Network defaults

- Dual-stack TUN with IPv4-preferred DNS resolution
- Native sing-tun TCP/IP stack (sing-box 1.15+, with the deprecated `stack` field omitted)
- MTU `1400`
- UDP session timeout `5m`

MagicNet may override these defaults through `.config/magicnet/network-policy.conf`.
