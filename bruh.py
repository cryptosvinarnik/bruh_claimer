import json

import yaml
from httpx import Client
from loguru import logger
from web3 import Web3

from data.config import HEADERS


RPC_URL = yaml.safe_load(open("config.yaml").read())["RPC_URL"]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
client = Client(headers=HEADERS)

contract = w3.eth.contract(
    address=Web3.toChecksumAddress("0x0857832548ab9dd3724943305b1ca5d230341b90"),
    abi=json.loads(open("data/abi.json").read())
)


def get_claim_data(address: str) -> dict:
    return client.post(
        "https://bruhcoin.co/api/sinature",
        params={"userAddress": address},
        timeout=15
    )


def claim_tokens(private_key: str):
    account = w3.eth.account.from_key(private_key)

    logger.info(f"Claiming tokens for {account.address}")
    data = get_claim_data(account.address)

    logger.debug(data.text)

    json_data = data.json()

    if json_data.get("errorMsg") == "Not started":
        logger.error(f"Claim not started. Wait until 5:10 PM UTC.")
        exit(0)

    if json_data.get("errorMsg") == "Not eligible":
        logger.error(f"{account.address} Not eligible.")
        return

    data = contract.functions.claim(
        int(json_data["nonce"]),
        json_data["signature"],
        Web3.toChecksumAddress(HEADERS["Referer"].split("=")[-1]),
    )._encode_transaction_data()

    tx = {
        "chainId": 42161,
        "from": account.address,
        "to": contract.address,
        "data": data,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(account.address),
    }


    for _ in range(3):
        try:
            gas = w3.eth.estimate_gas(tx)
            break
        except Exception as e:
            logger.info(f"Retrying gas estimation {e}")
    else:
        logger.error("Failed to estimate gas")
        return

    logger.info(f"Estimated gas: {gas}")

    tx["gas"] = int(gas * 1.15)

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    logger.success(f"Transaction sent: {tx_hash.hex()}")
