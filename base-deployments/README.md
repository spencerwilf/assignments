# Base Token Deployments

Write a function in python that takes as input a Base block number and returns all token and
pool deployments. For token deployments, include the symbol, name, deployer address, token
address, block number, block hash, transaction hash and timestamp. For pool deployments,
include all of the previous information for the main token and also include the pool transaction
hash, pool block hash, pool block number and the paired token in the pool (WETH/USDC/etc).

## External files

A standard ERC20 ABI (erc20_abi.json) to call ERC20-specific functions to gather token information (symbol, name, etc)

Uniswap V3 Factory ABI to track the creation of new liquidity pools (0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1)

## Resources

https://web3py.readthedocs.io/en/stable/

## Broad methodology

1. To monitor token creations, we begin by instantiating the selected block and fetching all of its transactions:
    ```
    block = provider.eth.get_block(block_number, full_transactions=True)
    for tx in block.transactions:
    ```

2. From here, we want to filter out contract creations, and more specifically ERC20 contract creations. Contract creations on EVM-compatible chains have an empty "to" field, so we can filter according to this using the following line of code:
    ```
    if tx.to is None:
    ```
Additionally, we will want to check if the contract is an ERC20 deployment. ERC20s have standard properties such as "name" and "symbol", so we can use the following utility function to test if the deployment is an ERC20:
    ```
    def is_erc20_contract(address):
    try:
        contract = provider.eth.contract(address=address, abi=erc20_abi)
        symbol = contract.functions.symbol().call()
        name = contract.functions.name().call()
        return True, symbol, name
    except Exception as e:
        return False, None, None
    ```
As we will be outputting the token symbol and name eventually, we return them here to use them later.

3. Once we have our token deployment information, we move on to recording pool deployments. When a user adds liquidity, LP tokens are minted, which we don't want to record—we just want to record the creation of the pool itself. We can filter out LP token minting by the `Mint` event, which the original pool creation doesn't have. The logic for skipping LP token creation is below:
    ```
            for log in receipt.logs:
            if log.topics[0].hex() == mint_event_topic:
                has_mint_event = True
                break  # Found a Mint event, skip further processing for this transaction

        if has_mint_event:
            continue  # Skip this transaction as it's related to Uniswap V3 LP token minting
    ```

4. Pool creations can be distingished by the `PoolCreated` event. The logic for locating these events and extracting information out of them can be found below:
    ```
        if log.topics[0].hex() == pool_created_topic:
        token0_address = '0x' + log.topics[1].hex()[-40:]
        token1_address = '0x' + log.topics[2].hex()[-40:]
        token0_name, token0_symbol = get_token_details(token0_address)
        token1_name, token1_symbol = get_token_details(token1_address)
    ```

## How to call the function

At the bottom of the file , change the `block_number` variable to any block number
```
block_number = 5037210
```

## Output sample

### Token deployment
    ```
    [
    {
        "Type": "Token Creation",
        "Token address": "0xAC1Bd2486aAf3B5C0fc3Fd868558b082a531B2B4",
        "Name": "Toshi",
        "Symbol": "TOSHI",
        "Deployer": "0xbD11CeD0A5021CD7262c64576a79d5Dc3Bb5856C",
        "Transaction hash": "0xff18afa50dafd4295051dccf590be3ae0674fc119703e656fdec72dbd2618dc9",
        "Block Number": 5037210,
        "Block Hash": "0xa26a2c0eb2d3abab3daabda8ae4216cd1d3c17323163b0cd89ebdc5830efc20d",
        "Timestamp": 1696863767
    }
    ]
    ```

### Liquidity pool deployment
    ```
    [
    {
        "Type": "Pool Creation",
        "Token address": "0x4ed4e862860bed51a9570b96d89af5e1b0efefed",
        "Token name": "Degen",
        "Token symbol": "DEGEN",
        "Paired token": "WETH",
        "Pool address": "0xc9034c3e7f58003e6ae0c8438e7c8f4598d5acaa",
        "Transaction hash": "0xca09cd4ac1f29af786849958dc97fae051c004f4fce19e8b71b41e4aa2b47446",
        "Block number": 8933249,
        "Block hash": "0x797ada3c5e19448883200024e2cfc03f6f438067076d7f459f97638139c417ad",
        "Timestamp": 1704655845
    }
    ]
    ```
