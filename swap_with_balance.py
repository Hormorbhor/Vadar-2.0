# corrected_swap_with_balance.py - Fixed for Recall API

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RECALL_API_KEY")
# Use sandbox for initial testing and verification
BASE_URL = os.getenv("RECALL_API_URL", "https://api.sandbox.competitions.recall.network")

print(f"🌐 Using API URL: {BASE_URL}")
print(f"🔑 API Key configured: {'✅' if API_KEY else '❌'}")

def token_address(symbol):
    """Get token address for a given symbol"""
    return {
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "DAI":  "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    }.get(symbol.upper(), "")

def get_portfolio():
    """
    Get full portfolio from Recall API
    
    Returns:
        dict: Portfolio data or empty dict if error
    """
    endpoint = f"{BASE_URL}/api/agent/portfolio"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        print(f"📡 Fetching portfolio from: {endpoint}")
        response = requests.get(endpoint, headers=headers, timeout=30)
        
        print(f"📋 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Portfolio fetched successfully!")
            
            if data.get("success"):
                total_value = data.get("totalValue", 0)
                tokens = data.get("tokens", [])
                print(f"💰 Total portfolio value: ${total_value:,.2f}")
                print(f"🪙 Number of tokens: {len(tokens)}")
                
                for token in tokens:
                    symbol = token.get("symbol", "Unknown")
                    amount = token.get("amount", 0)
                    value = token.get("value", 0)
                    print(f"   • {symbol}: {amount:.4f} (${value:.2f})")
                
                return data
            else:
                print(f"❌ API returned error: {data}")
                return {}
        elif response.status_code == 404:
            print("❌ Portfolio endpoint not found (404)")
            print("💡 This might mean you need to:")
            print("   1. Register at https://register.recall.network/")
            print("   2. Verify your account by making your first trade")
            print("   3. Use the correct API URL")
            return {}
        elif response.status_code == 401:
            print("❌ Authentication failed (401)")
            print("💡 Check your API key in .env file")
            return {}
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error fetching portfolio: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error fetching portfolio: {e}")
        return {}

def get_balance(token, chain="evm"):
    """
    Get token balance from portfolio data (no separate balance endpoint)
    
    Args:
        token (str): Token symbol
        chain (str): Blockchain (default: "evm")
    
    Returns:
        float: Token balance, or 0.0 if error
    """
    # Get balance from portfolio endpoint since there's no separate balance endpoint
    portfolio = get_portfolio()
    if portfolio and portfolio.get("success"):
        tokens = portfolio.get("tokens", [])
        for token_data in tokens:
            if token_data.get("symbol", "").upper() == token.upper():
                balance = float(token_data.get("amount", 0))
                print(f"💰 {token} balance: {balance:.4f}")
                return balance
    
    print(f"💰 {token} balance: 0.0000 (not found in portfolio)")
    return 0.0

def get_token_price(symbol, chain="evm", specific_chain="eth"):
    """
    Get token price from Recall API
    
    Args:
        symbol (str): Token symbol (USDC, DAI, WETH)
        chain (str): Blockchain type (default: "evm")
        specific_chain (str): Specific chain (default: "eth")
    
    Returns:
        float: Token price in USD, or 0.0 if error
    """
    token_addr = token_address(symbol)
    if not token_addr:
        print(f"❌ Unknown token symbol: {symbol}")
        return 0.0

    endpoint = f"{BASE_URL}/api/price"
    params = {
        "token": token_addr,
        "chain": chain,
        "specificChain": specific_chain
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and "price" in result:
                price = float(result["price"])
                print(f"💰 {symbol} price: ${price:.4f}")
                return price
            else:
                print(f"❌ Price API error for {symbol}: {result.get('error', 'Unknown error')}")
                return 0.0
        else:
            print(f"❌ Price fetch failed for {symbol}: HTTP {response.status_code}")
            return 0.0
            
    except Exception as e:
        print(f"❌ Error fetching {symbol} price: {e}")
        return 0.0

def perform_swap(from_token, to_token, amount, chain="evm"):
    """
    Execute a token swap using the Recall API
    
    Args:
        from_token (str): Source token symbol
        to_token (str): Destination token symbol  
        amount (float): Amount to swap
        chain (str): Blockchain (default: "evm")
    
    Returns:
        str: Result message
    """
    # Check if we have enough balance first
    current_balance = get_balance(from_token)
    if current_balance < amount:
        return f"❌ Insufficient balance: {current_balance:.4f} {from_token} < {amount:.4f} required"
    
    endpoint = f"{BASE_URL}/api/trade/execute"
    payload = {
        "fromToken": token_address(from_token),
        "toToken": token_address(to_token),
        "amount": str(amount),
        "reason": f"Trading {amount} {from_token} to {to_token} via enhanced AI bot"
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    print(f"🔄 Executing swap: {amount} {from_token} -> {to_token}")
    print(f"📡 Endpoint: {endpoint}")
    
    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        print(f"📦 Response status: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            
            if result.get("success"):
                transaction = result.get("transaction", {})
                tx_id = transaction.get("id", "Unknown")
                from_amount = transaction.get("fromAmount", amount)
                to_amount = transaction.get("toAmount", "Unknown")
                
                return f"✅ Swap successful! Tx: {tx_id}\n   Swapped: {from_amount} {from_token} -> {to_amount} {to_token}"
            else:
                error_msg = result.get("error", "Unknown failure")
                return f"❌ Swap failed: {error_msg}"
        elif resp.status_code == 400:
            print(f"❌ Bad request (400): {resp.text}")
            return f"❌ Invalid trade parameters: {resp.text}"
        elif resp.status_code == 401:
            return f"❌ Authentication failed - check your API key"
        elif resp.status_code == 404:
            return f"❌ Trade endpoint not found - check API URL"
        else:
            print(f"📦 Raw response: {resp.text}")
            return f"❌ HTTP Error {resp.status_code}: {resp.text}"
            
    except requests.exceptions.RequestException as e:
        return f"❌ Network error during swap: {e}"
    except Exception as e:
        return f"❌ Error during swap: {e}"

def verify_account():
    """
    Verify account by making a small test trade (as required by Recall)
    """
    print("🔍 ACCOUNT VERIFICATION")
    print("="*30)
    
    # Check if we have any USDC to trade
    usdc_balance = get_balance("USDC")
    
    if usdc_balance >= 1.0:
        print(f"💰 Found {usdc_balance:.2f} USDC - attempting verification trade")
        
        # Make a small trade to verify account
        result = perform_swap("USDC", "WETH", 1.0)
        print(f"🔄 Verification trade result: {result}")
        
        if "successful" in result.lower():
            print("✅ Account verified successfully!")
            return True
        else:
            print("❌ Verification trade failed")
            return False
    else:
        print(f"⚠️ Insufficient USDC balance ({usdc_balance:.4f}) for verification")
        print("💡 You may need initial funding in your competition account")
        return False

def diagnose_setup():
    """Complete setup diagnosis"""
    print("🩺 RECALL TRADING BOT DIAGNOSIS")
    print("="*40)
    
    # 1. Check environment
    print("1. 🔍 Environment Check:")
    print(f"   API Key: {'✅ Configured' if API_KEY else '❌ Missing'}")
    print(f"   API URL: {BASE_URL}")
    
    if not API_KEY:
        print("\n❌ Missing API key! Steps to fix:")
        print("   1. Register at: https://register.recall.network/")
        print("   2. Get your API key from account page")
        print("   3. Add to .env file: RECALL_API_KEY=your_key_here")
        return
    
    # 2. Test API connection
    print("\n2. 📡 API Connection Test:")
    portfolio = get_portfolio()
    
    if portfolio.get("success"):
        print("   ✅ API connection working!")
        
        # 3. Check portfolio
        print("\n3. 💰 Portfolio Status:")
        tokens = portfolio.get("tokens", [])
        total_value = portfolio.get("totalValue", 0)
        
        if total_value > 0:
            print(f"   ✅ Portfolio value: ${total_value:.2f}")
            print("   ✅ Ready to trade!")
        else:
            print("   ⚠️ Empty portfolio - you may need initial funding")
            print("   💡 Contact Recall support for competition funding")
    else:
        print("   ❌ API connection failed!")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Verify you're registered at https://register.recall.network/")
        print("   2. Check your API key is correct")
        print("   3. Make sure you're accepted into competition")
        print("   4. Try sandbox URL: https://api.sandbox.competitions.recall.network")

# Legacy function for backward compatibility
def swap_tokens(from_token, to_token, amount):
    """Legacy function - use perform_swap instead"""
    return perform_swap(from_token, to_token, amount)

if __name__ == "__main__":
    print("🧪 Running complete diagnosis...")
    diagnose_setup()
    
    print("\n" + "="*50)
    print("🧪 Testing functions...")
    
    # Test prices (should work even with empty portfolio)
    print("\n💰 Testing price fetching:")
    for token in ["USDC", "DAI", "WETH"]:
        price = get_token_price(token)
    
    print("\n✅ Diagnosis complete!")
    print("\n💡 Next steps:")
    print("1. If portfolio is empty, contact Recall for competition funding")
    print("2. Update .env with: RECALL_API_URL=https://api.sandbox.competitions.recall.network")
    print("3. Test with: TEST_MODE=true python enhanced_autonomous_agent.py")