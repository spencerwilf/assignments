# Arbitrum Swaps

Write a function in python that takes as input a Arbitrum block number and returns all camelot
token swaps on that block. For each token swap include the block number, block hash,
transaction hash, number of tokens swapped, trader address, token address, token pool
address and timestamp.

# External files

Camelot Router ABI: To be able to interface with the Camelot V3 router to track swaps

ERC20 ABI: Used to gather token information

Pool Contract ABI: Used to derive liquidity pool addresses

# Resources

https://docs.camelot.exchange/

https://web3py.readthedocs.io/en/stable/


## Broad methodology

1. We begin by instantiating the passed in block number and looping through the block's transactions.
    ```
    block = provider.eth.get_block(block_number, full_transactions=True)
    
    for tx in block.transactions:
        receipt = provider.eth.get_transaction_receipt(tx.hash)
        trader_address = receipt['from'].lower()
    ```

2. We then loop through the transaction's logs, looking for swap events originating from the Camelot V3 Router
    ```
        for log_index, log in enumerate(receipt.logs):  
            if log.topics[0].hex() == swap_topic and '0x' + log.topics[1].hex()[-40:] == camelot_router_contract.address.lower():
                # Log to extract other relevant information
    ```

3. Most of the required data is relatively straightforward to locate, but ascertaining the token pool address is more complicated, as we can't ascertain it from log data. The chosen approach was to track Transfer events, monitoring which token the address initially interacting with the Camelot V3 Router initially sent, as well as the token it ended up receiving. Relevant logic is below:
    ```
        for log_index, log in enumerate(receipt.logs):
            if log.topics[0].hex() == transfer_topic:
                from_address = '0x' + log.topics[1].hex()[-40:]
                to_address = '0x' + log.topics[2].hex()[-40:]
                transfers[log_index] = {
                    "from": from_address.lower(),
                    "to": to_address.lower(),
                    "token_address": log.address.lower()
                }
        
        # other code

            for transfer_log_index, transfer_details in transfers.items():
                if transfer_details['to'] == trader_address:
                    token_received_address = transfer_details['token_address']
                if transfer_details['from'] == trader_address:
                    token_sent_address = transfer_details['token_address']
    ```
Using the Transfer logs, we are able to ascertain the information needed to compute the pool address using the `pool` contract. The logic for this computation is below:

    ```
        if token_received_address and token_sent_address:
            pool_address = get_pool_by_pair(token_sent_address, token_received_address)
            token_sent_decimals = get_token_decimals(token_sent_address)
            adjusted_amount_received = adjust_token_amount(decoded_data[1], token_sent_decimals)
            token_name = get_token_name(token_sent_address)
    ```

## How to call the function

At the bottom of the file , change the `block_number` variable to any block number
```
block_number = 182150274
```

## Output sample

```
{
    "Block number": 182180433,
    "Block hash": "0x2d681bd1ae2a3f54fb60039d98928a6ee7ef73262269dec397f05d4b919b0c60",
    "Transaction hash": "0x6faace1090333b5020871bac54fca47337067f3627950036df47e5e19a0cf986",
    "Trader address": "0x004df5de266316d7aa68a639ad73d795a631e2e6",
    "Token name": "Xai",
    "Token address": "0x4cb9a7ae498cedcbb5eae9f25736ae7d428c9d66",
    "Amount token received": 0.7398830836370277,
    "Pool address": "0xba1CF57b1A7401Cc24622366808CeA1f209a2c50",
    "Block timestamp": 1708306651
}
```