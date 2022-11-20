from brownie import config, network, interface
from scripts.helpful_scripts import get_account
from scripts.getweth import get_weth
from web3 import Web3

amount = Web3.toWei(0.08, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork-deve"]:
        get_weth()

    lending_pool = get_lending_pool()
    print(lending_pool)

    approve_tx = approve_erc20(lending_pool.address, amount, erc20_address, account)

    print("Depositing")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited")

    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    print("Borrowing")

    dai_eth_pricefeed = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_pricefeed"]
    )

    amount_dai_to_borrow = 1 / dai_eth_pricefeed * (borrowable_eth * 0.95)
    print(f"Going to borrow {amount_dai_to_borrow} dai")

    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        2,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print(f"We have borrowed {amount_dai_to_borrow} dai")
    get_borrowable_data(lending_pool, account)

    repay_all(amount, lending_pool, account)


def repay_all(amount, lendingpool, account):
    approve_erc20(
        lendingpool,
        amount,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lendingpool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        2,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Repaid")


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_address"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(spender, amount, erc20_address, account):
    print("Approving erc-20 token")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved")
    return tx


def get_borrowable_data(lendingpool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lendingpool.getUserAccountData(account.address)

    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))


def get_asset_price(pricefeed):
    dai_eth_pricefeed = interface.AggregatorV3Interface(pricefeed)
    latest_value = dai_eth_pricefeed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_value, "ether")
    print(f"The current value of dai/eth is {converted_latest_price}")
    return float(latest_value)
