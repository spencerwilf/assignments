import requests, json

def find_liquidity_pairs(token_address):
    liquidity_pairs_info = []

    base_url = 'https://api.dexscreener.com/latest/dex/tokens/'
    response = requests.get(f"{base_url}{token_address}")

    if response.status_code != 200:
        print(f"Failed to fetch token data: HTTP {response.status_code}")
        return liquidity_pairs_info

    data = response.json()
    pairs = data.get('pairs', [])

    for pair in pairs:
        pair_address = pair.get('pairAddress')
        chain_id = pair.get('chainId', 'sol')
        pair_response = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_address}")

        if pair_response.status_code != 200:
            print(f"Failed to fetch data for pair {pair_address}: HTTP {pair_response.status_code}")
            continue

        pair_data = pair_response.json()
        if not pair_data.get('pairs'):
            continue

        first_pair = pair_data['pairs'][0]

        base_token_address = first_pair.get('baseToken', {}).get('address', '').lower()
        if base_token_address == token_address.lower():
            dex = first_pair.get('dexId', 'Unknown DEX ID')
            liquidity_pairs_info.append({'Pair address': pair_address, "DEX": dex})

    return liquidity_pairs_info

# Change to whatever token address you want
token_address = '4vqYQTjmKjxrWGtbL2tVkbAU1EVAz9JwcYtd2VE3PbVU'

transfers = find_liquidity_pairs(token_address)
print(json.dumps(transfers, indent=4))