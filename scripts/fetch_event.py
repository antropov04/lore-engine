#!/usr/bin/env python3
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ETHERSCAN_KEY = os.environ["ETHERSCAN_API_KEY"]
BASE = "https://api.etherscan.io/v2/api"
CHAIN_ID = 1

ETH_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"


def eth_usd() -> float:
    try:
        r = requests.get(ETH_PRICE_URL, timeout=10)
        return float(r.json()["ethereum"]["usd"])
    except Exception:
        return 3500.0


def _get(params: dict) -> dict:
    params = {**params, "chainid": CHAIN_ID, "apikey": ETHERSCAN_KEY}
    r = requests.get(BASE, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("status") == "0" and "message" in data and data.get("message") != "OK":
        if data.get("message") == "No transactions found":
            return data
        raise RuntimeError(f"Etherscan error: {data.get('message')} / {data.get('result')}")
    return data


def fetch_tx(tx_hash: str) -> dict:
    resp = _get({"module": "proxy", "action": "eth_getTransactionByHash", "txhash": tx_hash})
    tx = resp.get("result")
    if not isinstance(tx, dict):
        raise RuntimeError(f"tx not found: {tx_hash}: {resp}")

    time.sleep(0.25)
    resp = _get({"module": "proxy", "action": "eth_getTransactionReceipt", "txhash": tx_hash})
    receipt = resp.get("result") or {}

    time.sleep(0.25)
    block_hex = tx["blockNumber"]
    resp = _get({
        "module": "proxy",
        "action": "eth_getBlockByNumber",
        "tag": block_hex,
        "boolean": "false",
    })
    block = resp.get("result") or {}
    ts = int(block["timestamp"], 16) if block.get("timestamp") else int(time.time())

    value_eth = int(tx["value"], 16) / 1e18
    gas_used = int(receipt.get("gasUsed", "0x0"), 16)
    gas_price = int(tx.get("gasPrice", "0x0"), 16)
    gas_eth = (gas_used * gas_price) / 1e18

    price = eth_usd()

    log_count = len(receipt.get("logs", []))
    if log_count == 0:
        event_type = "transfer" if value_eth > 0 else "contract_call"
    elif log_count > 50:
        event_type = "exploit_candidate"
    elif log_count > 10:
        event_type = "swap_or_complex"
    else:
        event_type = "token_transfer"

    return {
        "tx_hash": tx_hash,
        "from_addr": tx["from"],
        "to_addr": tx.get("to") or "contract_creation",
        "value_eth": round(value_eth, 4),
        "value_usd": round(value_eth * price, 2),
        "gas_eth": round(gas_eth, 6),
        "gas_usd": round(gas_eth * price, 2),
        "block_number": int(block_hex, 16),
        "timestamp_iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        "event_type": event_type,
        "log_count": log_count,
        "eth_price_used": price,
    }


def fetch_latest_for_address(address: str) -> dict:
    resp = _get({
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 10,
        "sort": "desc",
    })
    txs = resp.get("result") or []
    if not isinstance(txs, list) or not txs:
        raise RuntimeError(f"no recent txs for {address}: {resp}")
    biggest = max(txs, key=lambda t: int(t.get("value", "0")))
    event = fetch_tx(biggest["hash"])
    event["address_context"] = address
    return event


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: fetch_event.py <0x...>", file=sys.stderr)
        sys.exit(2)

    target = sys.argv[1].strip().lower()
    if not target.startswith("0x"):
        print("input must start with 0x", file=sys.stderr)
        sys.exit(2)

    if len(target) == 66:
        event = fetch_tx(target)
    elif len(target) == 42:
        event = fetch_latest_for_address(target)
    else:
        print(f"unrecognized length {len(target)}", file=sys.stderr)
        sys.exit(2)

    out = Path.cwd() / "event.json"
    out.write_text(json.dumps(event, indent=2))
    print(f"OK: event written to {out}")
    print(json.dumps(event, indent=2))


if __name__ == "__main__":
    main()
