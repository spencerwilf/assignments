from web3 import Web3
import json

with open('camelot_router_abi.json', 'r') as abi_file:
    camelot_router_abi = json.load(abi_file)

with open('pool_contract_abi.json', 'r') as pool_abi_file:
    pool_abi = json.load(pool_abi_file)

with open('erc20_abi.json', 'r') as erc20_abi_file:
    erc20_abi = json.load(erc20_abi_file)

provider = Web3(Web3.HTTPProvider("https://arb-mainnet.g.alchemy.com/v2/C7EDrV8VssNi0A0Esjv01xqB3P3oizpN"))

# Camelot factory contract needed to get token pool pairs
factory_contract = provider.eth.contract(
    address="0x1a3c9B1d2F0529D97f2afC5136Cc23e58f1FD35B",
    abi=pool_abi
)

# Camelot router
camelot_router_contract = provider.eth.contract(
    address="0x1F721E2E82F6676FCE4eA07A5958cF098D339e18",
    abi=pool_abi
)

def get_token_decimals(token_address):
    checksum_address = Web3.to_checksum_address(token_address)
    token_contract = provider.eth.contract(address=checksum_address, abi=erc20_abi)
    decimals = token_contract.functions.decimals().call()
    return decimals

def get_token_name(token_address):
    checksum_address = Web3.to_checksum_address(token_address)
    token_contract = provider.eth.contract(address=checksum_address, abi=erc20_abi)
    name = token_contract.functions.name().call()
    return name

def adjust_token_amount(raw_amount, decimals):
    adjusted_amount = raw_amount / (10 ** decimals)
    return adjusted_amount


# Function to call `factory_contract` to get the token pool address
def get_pool_by_pair(token_address1, token_address2):
    pool_address = factory_contract.functions.poolByPair(
        Web3.to_checksum_address(token_address1),
        Web3.to_checksum_address(token_address2)
    ).call()
    return pool_address

# Generates Swap event signature
def get_swap_event_topic():
    swap_event_signature = "Swap(address,address,int256,int256,uint160,uint128,int24)"
    swap_event_topic = provider.keccak(text=swap_event_signature).hex()
    return swap_event_topic

# Generates Transfer event signature: used to derive the tokens transferred to and from a user to ascertain the token pool address
def get_transfer_event_topic():
    transfer_event_signature = "Transfer(address,address,uint256)"
    transfer_event_topic = provider.keccak(text=transfer_event_signature).hex()
    return transfer_event_topic

# Parses the data fields in swap logs
def parse_log_data(log):
    types = ['int256', 'int256', 'uint160', 'uint128', 'int24']
    decoded_data = provider.codec.decode(types, log['data'])
    return decoded_data

def get_swaps_for_block(block_number):
    swap_topic = get_swap_event_topic()
    transfer_topic = get_transfer_event_topic()

    block = provider.eth.get_block(block_number, full_transactions=True)
    block_timestamp = block.timestamp

    swaps = []
    unique_txs = set()
    
    # block.transactions: gets transaction objects included in a block
    for tx in block.transactions:
        
        receipt = provider.eth.get_transaction_receipt(tx.hash)
        trader_address = receipt['from'].lower()

        # take log where user is the sender of tokens—recipient in that address will be the LP address!

        # Dictionary to hold transfer events, keyed by log index within the transaction
        transfers = {}
        token_received_address = None
        lp_address = None
        # Pass to gather transfer events
        for log_index, log in enumerate(receipt.logs):
            if log.topics[0].hex() == transfer_topic:
                from_address = '0x' + log.topics[1].hex()[-40:]
                to_address = '0x' + log.topics[2].hex()[-40:]
                transfers[log_index] = {
                    "from": from_address.lower(),
                    "to": to_address.lower(),
                    "token_address": log.address.lower()
                }

        # Now process Swap events
        for log_index, log in enumerate(receipt.logs):
            
            if log.topics[0].hex() == swap_topic:
                decoded_data = parse_log_data(log)
                
                for transfer_log_index, transfer_details in transfers.items():
                    if transfer_details['from'] == trader_address:
                        token_received_address = transfer_details['token_address']
                        lp_address = transfer_details['to']

                if token_received_address and lp_address:
                    if receipt.transactionHash.hex() in unique_txs:
                        continue
                    unique_txs.add(receipt.transactionHash.hex())
            
                    token_received_decimals = get_token_decimals(token_received_address)
                    adjusted_amount_received = adjust_token_amount(max(decoded_data[0], decoded_data[1]), token_received_decimals)
                    token_name = get_token_name(token_received_address)

                    swap_details = {
                        "Block number": block_number,
                        "Block hash": log.blockHash.hex(),
                        "Transaction hash": log.transactionHash.hex(),
                        "Trader address": trader_address,
                        "Token name": token_name,
                        "Token address": token_received_address,
                        "Amount token received": adjusted_amount_received,
                        "Pool address": lp_address,
                        "Block timestamp": block_timestamp
                    }
                    swaps.append(swap_details)
                else:
                    print('Tokens not found')

    return swaps

block_number = 163872381        # Replace with the block number you're interested in
swaps = get_swaps_for_block(block_number)
for swap in swaps:
    print(json.dumps(swap, indent=4))