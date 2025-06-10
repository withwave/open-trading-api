# -*- coding: utf-8 -*-
"""
MCP-kis main application script.

This script demonstrates basic usage of the KIS API:
1. Authenticates using credentials from kis_devlp.yaml.
2. Fetches and prints the current stock balance.
3. Fetches and prints the current price for a sample stock (e.g., Samsung Electronics 005930).

To use this script:
- Ensure you have a Python virtual environment set up with necessary packages (see requirements.txt).
- Configure your API keys, account numbers, and trading_mode ('mock' or 'real')
  in MCP-kis/kis_devlp.yaml.
- Run the script: python MCP-kis/main.py
"""
import kis_auth as ka
import kis_domstk as kb # For domestic stock APIs
# To use other APIs like overseas stocks, futures, etc., you would import other modules
# similar to kis_domstk.py (e.g., kis_ovrseastk.py) if they exist and are copied.

import pandas as pd
import sys
import os

def main():
    # Authenticate: Token is issued and environment (mock/real) is set based on kis_devlp.yaml
    # The product code (e.g., "01" for stocks) can be passed if different from default in YAML
    # ka.auth(product="01")
    if not ka.auth(): # If auth fails, it might print an error and return, or raise an exception
        print("Authentication failed. Please check your credentials and configuration in kis_devlp.yaml.")
        # Attempt to load environment details for context, even if auth failed
        try:
            print(f"Attempted Trading Environment: {'Paper Trading' if ka.isPaperTrading() else 'Real Trading'}")
            print(f"Attempted Account: {ka.getTREnv().my_acct}, Product Code: {ka.getTREnv().my_prod if ka.getTREnv() else 'N/A'}")
        except Exception as e:
            print(f"Could not retrieve environment details: {e}")
        return

    print(f"Authentication successful. Trading Environment: {'Paper Trading' if ka.isPaperTrading() else 'Real Trading'}")
    print(f"Using Account: {ka.getTREnv().my_acct}, Product Code: {ka.getTREnv().my_prod}")

    # Example 1: Fetch and print stock balance (list of holdings)
    print("\nFetching stock balance...")
    balance_data = kb.get_inquire_balance_lst() # Default fetches 'ALL' if specific account/product not passed
    if balance_data is not None and not balance_data.empty:
        print("Current stock holdings:")
        print(balance_data)
    elif balance_data is not None: # It could be an empty DataFrame
        print("No stock holdings found or an issue occurred (e.g., empty balance).")
    else: # API call might have failed and returned None
        print("Failed to fetch stock balance. The API might have returned an error or None.")

    # Example 2: Fetch and print current price for a sample stock (e.g., Samsung Electronics: 005930)
    sample_stock_code = "005930"  # Example: Samsung Electronics
    print(f"\nFetching current price for stock code: {sample_stock_code}...")
    price_data = kb.get_inquire_price(itm_no=sample_stock_code)
    if price_data:
        # Assuming price_data is a namedtuple or object with attributes like stck_prpr, prdy_vrss
        try:
            # The actual attributes depend on the API response structure wrapped by get_inquire_price
            # Common attributes might be 'stck_prpr' (current price) and 'prdy_vrss' (change vs previous day)
            # These need to be verified against the actual return object of get_inquire_price
            print(f"Stock: {sample_stock_code}, Current Price: {getattr(price_data, 'stck_prpr', 'N/A')}, Change from Previous Day: {getattr(price_data, 'prdy_vrss', 'N/A')}")
        except AttributeError as e:
            print(f"Price data for {sample_stock_code} received, but format is unexpected: {e}")
            print(price_data)
    else:
        print(f"Failed to fetch price for stock code: {sample_stock_code}. The API might have returned an error or None.")

    # Add more MCP-specific logic here
    print("\nScript finished. Modify main.py to add your MCP logic.")

if __name__ == "__main__":
    # Ensure that the current directory (MCP-kis) is in the Python path
    # so that kis_auth and kis_domstk can be imported.
    # This is often necessary if running `python MCP-kis/main.py` from the project root.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Also, if MCP-kis is intended to be part of a larger package structure,
    # ensure the parent directory containing 'MCP-kis' is also in sys.path
    # For example, if your structure is /project_root/MCP-kis/main.py
    # and you run from /project_root: python MCP-kis/main.py
    # then imports within MCP-kis like `import kis_auth` should work.
    # If running from within MCP-kis: cd MCP-kis; python main.py
    # then the sys.path.insert above should be sufficient.

    main()
