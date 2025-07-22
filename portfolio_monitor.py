# portfolio_monitor.py

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot data structure"""
    timestamp: str
    total_value: float
    tokens: Dict[str, Dict[str, float]]  # token -> {amount, price, value}
    performance_24h: float
    performance_total: float

@dataclass
class TradeRecord:
    """Trade record data structure"""
    timestamp: str
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float
    price: float
    transaction_id: str
    success: bool

class PortfolioMonitor:
    """Monitor and track portfolio performance"""
    
    def __init__(self):
        self.api_key = os.getenv("RECALL_API_KEY")
        self.base_url = os.getenv("RECALL_API_URL", "https://api.competitions.recall.network")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Token addresses for API calls
        self.token_addresses = {
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        }
        
        # Data storage
        self.snapshots: List[PortfolioSnapshot] = []
        self.trades: List[TradeRecord] = []
        self.load_historical_data()
    
    def get_portfolio_from_api(self) -> Dict:
        """Get portfolio data from Recall API"""
        try:
            response = requests.get(
                f"{self.base_url}/api/agent/portfolio",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching portfolio: {e}")
            return {}
    
    def get_token_balance(self, token: str) -> float:
        """Get balance for a specific token"""
        try:
            token_addr = self.token_addresses.get(token)
            if not token_addr:
                return 0.0
                
            response = requests.get(
                f"{self.base_url}/api/balance",
                params={"token": token_addr, "chain": "evm"},
                headers=self.headers,
                timeout=30
            )
            
            data = response.json()
            if data.get("success"):
                return float(data.get("balance", 0))
            return 0.0
        except Exception as e:
            print(f"❌ Error fetching {token} balance: {e}")
            return 0.0
    
    def get_token_price(self, token: str) -> float:
        """Get current price for a token"""
        try:
            token_addr = self.token_addresses.get(token)
            if not token_addr:
                return 0.0
                
            response = requests.get(
                f"{self.base_url}/api/price",
                params={
                    "token": token_addr,
                    "chain": "evm",
                    "specificChain": "eth"
                },
                headers=self.headers,
                timeout=30
            )
            
            data = response.json()
            if data.get("success"):
                return float(data.get("price", 0))
            return 0.0
        except Exception as e:
            print(f"❌ Error fetching {token} price: {e}")
            return 0.0
    
    def create_portfolio_snapshot(self) -> PortfolioSnapshot:
        """Create a current portfolio snapshot"""
        try:
            tokens_data = {}
            total_value = 0
            
            for token in self.token_addresses.keys():
                balance = self.get_token_balance(token)
                price = self.get_token_price(token)
                value = balance * price
                
                tokens_data[token] = {
                    "amount": balance,
                    "price": price,
                    "value": value
                }
                total_value += value
            
            # Calculate performance
            performance_24h = 0
            performance_total = 0
            
            if len(self.snapshots) > 0:
                # 24h performance
                yesterday = datetime.now() - timedelta(hours=24)
                recent_snapshots = [
                    s for s in self.snapshots 
                    if datetime.fromisoformat(s.timestamp) >= yesterday
                ]
                
                if recent_snapshots:
                    old_value = recent_snapshots[0].total_value
                    if old_value > 0:
                        performance_24h = ((total_value - old_value) / old_value) * 100
                
                # Total performance
                initial_value = self.snapshots[0].total_value
                if initial_value > 0:
                    performance_total = ((total_value - initial_value) / initial_value) * 100
            
            snapshot = PortfolioSnapshot(
                timestamp=datetime.now().isoformat(),
                total_value=total_value,
                tokens=tokens_data,
                performance_24h=performance_24h,
                performance_total=performance_total
            )
            
            self.snapshots.append(snapshot)
            self.save_historical_data()
            
            return snapshot
            
        except Exception as e:
            print(f"❌ Error creating portfolio snapshot: {e}")
            return None
    
    def get_leaderboard(self) -> Dict:
        """Get competition leaderboard"""
        try:
            response = requests.get(
                f"{self.base_url}/api/competition/leaderboard",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching leaderboard: {e}")
            return {}
    
    def save_historical_data(self):
        """Save historical data to file"""
        try:
            data = {
                "snapshots": [asdict(s) for s in self.snapshots],
                "trades": [asdict(t) for t in self.trades]
            }
            
            with open("portfolio_history.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving historical data: {e}")
    
    def load_historical_data(self):
        """Load historical data from file"""
        try:
            if os.path.exists("portfolio_history.json"):
                with open("portfolio_history.json", "r") as f:
                    data = json.load(f)
                
                self.snapshots = [
                    PortfolioSnapshot(**s) for s in data.get("snapshots", [])
                ]
                self.trades = [
                    TradeRecord(**t) for t in data.get("trades", [])
                ]
        except Exception as e:
            print(f"❌ Error loading historical data: {e}")
    
    def display_dashboard(self):
        """Display portfolio dashboard"""
        try:
            snapshot = self.create_portfolio_snapshot()
            if not snapshot:
                print("❌ Failed to create portfolio snapshot")
                return
            
            print("\n" + "="*60)
            print("🏆 PORTFOLIO DASHBOARD")
            print("="*60)
            
            # Portfolio Overview
            print(f"\n📊 PORTFOLIO OVERVIEW")
            print(f"Total Value: ${snapshot.total_value:,.2f}")
            print(f"24h Performance: {snapshot.performance_24h:+.2f}%")
            print(f"Total Performance: {snapshot.performance_total:+.2f}%")
            print(f"Last Updated: {snapshot.timestamp}")
            
            # Token Breakdown
            print(f"\n💰 TOKEN BREAKDOWN")
            for token, data in snapshot.tokens.items():
                percentage = (data["value"] / snapshot.total_value * 100) if snapshot.total_value > 0 else 0
                print(f"{token:6}: {data['amount']:>10.4f} @ ${data['price']:>8.2f} = ${data['value']:>10.2f} ({percentage:5.1f}%)")
            
            # Recent Performance
            if len(self.snapshots) >= 2:
                print(f"\n📈 RECENT PERFORMANCE")
                recent_snapshots = self.snapshots[-10:]  # Last 10 snapshots
                for i, snap in enumerate(recent_snapshots[-5:], len(recent_snapshots)-4):
                    change = 0
                    if i > 0:
                        prev_value = recent_snapshots[i-1].total_value
                        if prev_value > 0:
                            change = ((snap.total_value - prev_value) / prev_value) * 100
                    
                    print(f"{snap.timestamp[:19]}: ${snap.total_value:>10.2f} ({change:+5.2f}%)")
            
            # Competition Stats
            leaderboard = self.get_leaderboard()
            if leaderboard.get("success"):
                print(f"\n🏆 COMPETITION STATUS")
                agents = leaderboard.get("leaderboard", [])
                if agents:
                    print(f"Total Participants: {len(agents)}")
                    
                    # Find our position
                    for i, agent in enumerate(agents, 1):
                        if agent.get("agentId") == leaderboard.get("agentId"):  # Assuming we can identify our agent
                            print(f"Current Rank: #{i}")
                            print(f"Our Performance: {agent.get('totalReturn', 0)*100:+.2f}%")
                            print(f"Sharpe Ratio: {agent.get('sharpeRatio', 0):.3f}")
                            break
                    
                    # Top 3
                    print(f"\nTop 3 Performers:")
                    for i, agent in enumerate(agents[:3], 1):
                        print(f"{i}. Agent {agent.get('agentId', 'Unknown')[:8]}: {agent.get('totalReturn', 0)*100:+.2f}%")
            
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error displaying dashboard: {e}")
    
    def monitor_continuously(self, interval_minutes: int = 5):
        """Continuously monitor portfolio"""
        print(f"🔄 Starting portfolio monitoring (every {interval_minutes} minutes)")
        
        while True:
            try:
                self.display_dashboard()
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                print("\n🛑 Portfolio monitoring stopped")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute on error

def main():
    """Main function for portfolio monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Portfolio Monitor for Recall Trading Bot")
    parser.add_argument("--interval", type=int, default=5, help="Monitoring interval in minutes")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    monitor = PortfolioMonitor()
    
    if args.once:
        monitor.display_dashboard()
    else:
        monitor.monitor_continuously(args.interval)

if __name__ == "__main__":
    main()