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

def extract_transfer_logs(receipt, trader_address, swap_contract_address):
    transfer_event_topic = get_transfer_event_topic()
    transfers_to_trader = []
    initial_token = None  # To store the token address that the trader initially sends

    for log in receipt.logs:
        # Check if it's a Transfer event
        if log.topics[0].hex() == transfer_event_topic:
            # Extract 'from' and 'to' addresses from the topics
            from_address = '0x' + log.topics[1].hex()[-40:]
            to_address = '0x' + log.topics[2].hex()[-40:]
            
            # The contract emitting this is the token contract
            token_address = log.address
            # Decode the transferred amount from the data field
            amount_hex = log['data'].hex() if isinstance(log['data'], bytes) else log['data']
            amount = int(amount_hex, 16)
            
            # Check if the trader is the sender, which means it's the token being swapped
            if from_address.lower() == trader_address.lower() and to_address.lower() == swap_contract_address.lower():
                initial_token = token_address
            
            # If the 'to' address is the trader, it's the token being received
            elif to_address.lower() == trader_address.lower():
                transfers_to_trader.append((token_address, amount))

    return initial_token, transfers_to_trader


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
    swap_contract_address = "0x1F721E2E82F6676FCE4eA07A5958cF098D339e18"  # Replace with your swap contract address

    for tx in block.transactions:
        receipt = provider.eth.get_transaction_receipt(tx.hash)
        trader_address = receipt['from'].lower()
        
        # Extract initial token sent and transfer events to the trader
        initial_token, transfers_to_trader = extract_transfer_logs(receipt, trader_address, swap_contract_address)

        # Process each token received by the trader to find pool addresses
        for token_address, amount in transfers_to_trader:
            if initial_token:
                pool_address = get_pool_by_pair(initial_token, token_address)
            else:
                pool_address = "Initial token not found"

            log_info = {
                'block_number': block_number,
                'block_hash': block.hash.hex(),
                'transaction_hash': tx.hash.hex(),
                'trader_address': trader_address,
                'token_address': token_address,
                'amount': amount,
                'pool_address': pool_address,
                'timestamp': provider.eth.get_block(block_number).timestamp
            }
            swap_logs.append(log_info)

    return swap_logs


block_number = 180927732    # Replace with the actual block number
swaps = get_swap_logs(block_number)
for swap in swaps:
    print(json.dumps(swap, indent=4))