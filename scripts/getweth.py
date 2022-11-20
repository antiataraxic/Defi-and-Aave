from brownie import config, interface, network
from scripts.helpful_scripts import get_account
from web3 import Web3

eth_to_deposit = Web3.toWei(0.08, "ether")


def get_weth():
    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"value": eth_to_deposit, "from": account})
    print("Received 0.08 Weth!")
    return tx


def main():
    get_weth()
