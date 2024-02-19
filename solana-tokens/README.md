# Solana Pool Information:

Given an SPL token mint address, find all associated pools (Raydium, Orca, Serum, etc). Feel
free to use any JSON RPC methods, external data APIs, etc

## API Used
https://docs.dexscreener.com/api/reference

## Broad Methodology

1. Query the following API endpoint to get LP pairs for a given token:

    https://api.dexscreener.com/latest/dex/tokens/:tokenAddreses

2. Iterate through the above API response, calling the following API route for each pair address to get the DEX associated with the pair address

    https://api.dexscreener.com/latest/dex/pairs/:chainId/:pairAddresses

