from web3 import Web3
import json

# Reading from the abi file
with open('camelot_router_abi.json', 'r') as abi_file:
    camelot_router_abi = json.load(abi_file)

with open('pool_contract_abi.json', 'r') as pool_abi_file:
    pool_abi = json.load(pool_abi_file)

# Establishing Arbitrum RPC connection
provider = Web3(Web3.HTTPProvider("https://arb-mainnet.g.alchemy.com/v2/C7EDrV8VssNi0A0Esjv01xqB3P3oizpN"))

factory_contract = provider.eth.contract(
    address="0x1a3c9B1d2F0529D97f2afC5136Cc23e58f1FD35B",
    abi=pool_abi
)

def get_pool_by_pair(token_address1, token_address2):
    pool_address = factory_contract.functions.poolByPair(
        Web3.to_checksum_address(token_address1),
        Web3.to_checksum_address(token_address2)
    ).call()
    return pool_address

def get_swap_event_topic():
    swap_event_signature = "Swap(address,address,int256,int256,uint160,uint128,int24)"
    swap_event_topic = provider.keccak(text=swap_event_signature).hex()
    return swap_event_topic

def extract_transfer_logs(receipt, trader_address):
    transfer_event_topic = get_transfer_event_topic()
    transfers_to_trader = []

    for log in receipt.logs:
        # Check if it's a Transfer event
        if log.topics[0].hex() == transfer_event_topic:
            # Extract the 'to' address from the topics and compare with trader_address
            to_address = '0x' + log.topics[2].hex()[-40:]
            if to_address.lower() == trader_address.lower():
                # The contract emitting this is the token contract
                token_address = log.address
                # Decode the transferred amount from the data field
                amount_hex = log['data'].hex() if isinstance(log['data'], bytes) else log['data']
                amount = int(amount_hex, 16)
                transfers_to_trader.append((token_address, amount))

    return transfers_to_trader

def get_transfer_event_topic():
    swap_event_signature = "Transfer(address,address,uint256)"
    swap_event_topic = provider.keccak(text=swap_event_signature).hex()
    return swap_event_topic


# Function to decode the data part of the log
def parse_log_data(log):
    types = ['int256', 'int256', 'uint160', 'uint128', 'int24']
    decoded_data = provider.codec.decode(types, log['data'])
    return decoded_data

# Function to fetch and decode swap logs
def get_swap_logs(block_number):
    swap_logs = []
    block = provider.eth.get_block(block_number, full_transactions=True)

    for tx in block.transactions:
        receipt = provider.eth.get_transaction_receipt(tx.hash)
        trader_address = receipt['from'].lower()
        
        # Extract transfer events to the trader
        transfers_to_trader = extract_transfer_logs(receipt, trader_address)

        for token_address, amount in transfers_to_trader:
            log_info = {
                'block_number': block_number,
                'block_hash': block.hash.hex(),
                'transaction_hash': tx.hash.hex(),
                'trader_address': trader_address,
                'token_address': token_address,
                'amount': amount,
                "pool_address": get_pool_by_pair(token_address, "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"),
                'timestamp': provider.eth.get_block(block_number).timestamp
            }
            swap_logs.append(log_info)
            
    return swap_logs

block_number = 180876266   # Replace with the actual block number
swaps = get_swap_logs(block_number)
for swap in swaps:
    print(json.dumps(swap, indent=4))