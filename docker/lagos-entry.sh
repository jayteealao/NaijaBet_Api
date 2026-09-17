#!/usr/bin/env bash
# Bring up the WireGuard tunnel from /run/wg/source.conf, prove the egress, run the command
# line given as arguments inside /work, and take the tunnel down on exit.
# The strip and the proof are the same lines as .github/workflows/live.yml.
set -euo pipefail

if [ ! -r /run/wg/source.conf ]; then
    echo "lagos: /run/wg/source.conf is missing; mount the WireGuard config there" >&2
    exit 2
fi

# Table = off: the Docker Desktop WSL2 kernel (5.15) lacks nft_fib_ipv4 and xt_connmark, so the
# firewall rules wg-quick adds for a 0.0.0.0/0 route fail (repro: `wg-quick up` inside this image
# ends with "Could not process rule" from nft and "CONNMARK not supported" from iptables-restore).
# The policy routing below is the part of wg-quick's add_default that the kernel does support.
mkdir -p /etc/wireguard
sed -e '/^DNS *=/d' -e 's/, *::\/0//' -e '/^\[Interface\]/a Table = off' /run/wg/source.conf \
    > /etc/wireguard/wg0.conf
chmod 600 /etc/wireguard/wg0.conf

wg-quick up wg0
trap 'wg-quick down wg0 >/dev/null 2>&1 || true' EXIT
wg set wg0 fwmark 51820
ip -4 route add 0.0.0.0/0 dev wg0 table 51820
ip -4 rule add not fwmark 51820 table 51820
ip -4 rule add table main suppress_prefixlength 0
# Docker's resolver sits on the host side, which the tunnel now hides; use the config's DNS (or 1.1.1.1).
DNS="$(sed -n 's/^DNS *= *//p' /run/wg/source.conf | tr ',' ' ' | awk '{print $1}')"
echo "nameserver ${DNS:-1.1.1.1}" > /etc/resolv.conf

UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
COUNTRY="$(curl -sS --max-time 30 https://ipinfo.io/country | tr -d '[:space:]')"
CODE="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 30 -A "$UA" https://sports.bet9ja.com/)"
echo "egress country=$COUNTRY bet9ja=$CODE"
if [ "$COUNTRY" != NG ] || [ "$CODE" != 200 ]; then
    echo "lagos: the egress proof failed; the command did not run" >&2
    exit 3
fi

# The command line comes from CMD in the environment (make lagos CMD="..."), or from the arguments.
# No exec: the EXIT trap must still run after the command.
cd /work
status=0
bash -c "${*:-${CMD:?lagos: set CMD to the shell line to run}}" || status=$?
exit "$status"
