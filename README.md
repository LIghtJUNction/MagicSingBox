# MagicSingBox
MagicNet x sing-box

## Network defaults

- Dual-stack TUN with IPv4-preferred DNS resolution
- `mixed` stack (system TCP and gVisor UDP)
- MTU `1400`
- UDP session timeout `5m`

MagicNet may override these defaults through `.config/magicnet/network-policy.conf`.
