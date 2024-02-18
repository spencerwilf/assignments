from web3 import Web3
import json

provider = Web3(Web3.HTTPProvider("https://base-mainnet.g.alchemy.com/v2/H4Z8XOXrgW5qYPUS9Nl0W29FHAgWbm1H"))

with open('erc20_abi.json', 'r') as erc20_abi_file:
    erc20_abi = json.load(erc20_abi_file)

with open('uniswap-v3-factory-abi.json', 'r') as v3_pool_file:
    v3_pool_abi = json.load(v3_pool_file)

# Uniswap V3 factory contract
factory_contract = provider.eth.contract(address='0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1', abi=v3_pool_abi)

# Verifying that a contract is an erc20
def is_erc20_contract(address):
    try:
        contract = provider.eth.contract(address=address, abi=erc20_abi)
        symbol = contract.functions.symbol().call()
        name = contract.functions.name().call()
        return True, symbol, name
    except Exception as e:
        return False, None, None

# When a liquidity pool is created, Uniswap LP tokens are naturally minted as well. This function will be used to filter out these LP token creations
def get_mint_event_topic():
    mint_event_signature = "Mint(address,uint256,uint256,uint256)"
    return provider.keccak(text=mint_event_signature).hex()

def get_pool_creation_event_topic():
    pool_created_event_signature = "PoolCreated(address,address,uint24,int24,address)"
    pool_created_event_topic = provider.keccak(text=pool_created_event_signature).hex()
    return pool_created_event_topic

# Used to get properties of the erc20
def get_token_details(contract_address):
    checksum_address = Web3.to_checksum_address(contract_address)
    contract = provider.eth.contract(address=checksum_address, abi=erc20_abi)
    name = contract.functions.name().call()
    symbol = contract.functions.symbol().call()
    return name, symbol

# Used to parse data section of the PoolCreated event
def parse_pool_created_data(log):
    types = ['int24', 'address']
    decoded_data = provider.codec.decode(types, log['data'])
    return decoded_data

# Main function
def get_token_creations_and_pool_deployments(block_number):
    pool_created_topic = get_pool_creation_event_topic()
    mint_event_topic = get_mint_event_topic()
    block = provider.eth.get_block(block_number, full_transactions=True)
    block_timestamp = block.timestamp

    creations = []
    processed_events = set()

    for tx in block.transactions:
        # Checking for contract creation (null 'to' field indicates contract creation)
        if tx.to is None:
            contract_address = provider.eth.get_transaction_receipt(tx.hash).contractAddress
            is_erc20, symbol, name = is_erc20_contract(contract_address)
            if is_erc20:
                creations.append({
                    "Type": "Token Creation",
                    "Token address": contract_address,
                    "Name": name,
                    "Symbol": symbol,
                    "Deployer": tx['from'],
                    "Transaction hash": tx.hash.hex(),
                    "Block Number": block.number,
                    "Block Hash": block.hash.hex(),
                    "Timestamp": block_timestamp
                })
                continue  # No need to further process tx

        receipt = provider.eth.get_transaction_receipt(tx.hash)
        has_mint_event = False

        # First pass to check Uniswap LP tokens being minted
        for log in receipt.logs:
            if log.topics[0].hex() == mint_event_topic:
                has_mint_event = True
                break  # Found a Mint event, skip further processing for this transaction

        if has_mint_event:
            continue  # Skip this transaction as it's related to Uniswap V3 LP token minting

        # Second pass for token and pool creations
        for log in receipt.logs:
            event_id = (tx.hash.hex(), log['logIndex'])  # logIndex for uniqueness
            if event_id in processed_events:
                continue  # Skip if this event has already been processed

            # Pool creation event
            if log.topics[0].hex() == pool_created_topic:
                token0_address = '0x' + log.topics[1].hex()[-40:]
                token1_address = '0x' + log.topics[2].hex()[-40:]
                token0_name, token0_symbol = get_token_details(token0_address)
                token1_name, token1_symbol = get_token_details(token1_address)

                decoded_data = parse_pool_created_data(log)
                creations.append({
                    "Type": "Pool Creation",
                    "Token address": token1_address,
                    "Token name": token1_name,
                    "Token symbol": token1_symbol,
                    "Paired token": token0_symbol,
                    "Pool address": decoded_data[1],
                    "Transaction hash": tx.hash.hex(),
                    "Block number": block.number,
                    "Block hash": block.hash.hex(),
                    "Timestamp": block_timestamp
                })
                processed_events.add(event_id)

    return creations


block_number = 5037210    # Replace with the block number you're interested in
transfers = get_token_creations_and_pool_deployments(block_number)
print(json.dumps(transfers, indent=4))


