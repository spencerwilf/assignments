# Solana Pool Information

Given an SPL token mint address, finds all associated pools (Raydium, Orca, Serum, etc).

## API Used
https://docs.dexscreener.com/api/reference

## Broad Methodology

1. Query the following API endpoint to get LP pairs for a given token:

    https://api.dexscreener.com/latest/dex/tokens/:tokenAddreses

2. Iterate through the above API response, calling the following API route for each pair address to get the DEX associated with the pair address

    https://api.dexscreener.com/latest/dex/pairs/:chainId/:pairAddresses


## How to call the function

At the bottom of the file , change the `token_address` variable to any Solana token address
```
token_address = '4vqYQTjmKjxrWGtbL2tVkbAU1EVAz9JwcYtd2VE3PbVU'
```

## Output sample
```
[
    {
        "Pair address": "EcHXwaRp26ChgAsmfdrVki44XRr8tibwJ17DbsUTiJGe",
        "DEX": "raydium"
    },
    {
        "Pair address": "BnfUT1mjfQ8oG3CmSw4SXmLKJj8QzWEHREGqZcba2KoC",
        "DEX": "orca"
    },
]
```
