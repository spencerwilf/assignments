import requests

# Replace with preferred token address
token_address = 'EPSTNDiuuNJHLSwdYxx22KKSvtzZ4SbeTLWXcp99T6qZ'

url = f'https://api.dexscreener.com/latest/dex/tokens/{token_address}'

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    
    pairs = data.get('pairs', [])
    
    for pair in pairs:
        pair_address = pair.get('pairAddress')
        chain_id = pair.get('chainId', 'sol')
        url = f'https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_address}'
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            pair_data = response.json()
            
            if pair_data.get('pairs'):  # Check if 'pairs' is not empty
                dex_id = pair_data['pairs'][0].get('dexId', 'Unknown DEX ID')
                print(f"Pair Address: {pair_address}, DEX ID: {dex_id}")
            else:
                print(f"No pairs found for Pair Address: {pair_address}")
        else:
            print(f"Failed to fetch data for pair {pair_address}: HTTP {response.status_code} - {response.reason}")

else:
    print(f"Failed to fetch data: HTTP {response.status_code} - {response.reason}")