# enhanced_autonomous_agent.py

import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain_groq import ChatGroq
from dataclasses import dataclass

# Import your existing modules - updated for correct API structure
from swap_with_balance import perform_swap, get_balance, get_token_price, get_portfolio

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Store market data for decision making"""
    prices: Dict[str, float]
    balances: Dict[str, float]
    total_portfolio_value: float
    timestamp: datetime

class EnhancedTradingAgent:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.1,  # Lower temperature for more consistent decisions
            model_name="llama3-70b-8192",
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Trading parameters
        self.supported_tokens = ["USDC", "DAI", "WETH"]
        self.min_trade_amount = 1.0
        self.max_trade_percentage = 0.3  # Max 30% of balance per trade
        self.profit_threshold = 0.02  # 2% profit threshold
        self.stop_loss_threshold = -0.05  # 5% stop loss
        
        # Performance tracking
        self.trade_history: List[Dict] = []
        self.initial_portfolio_value: Optional[float] = None
        
        # Initialize tools
        self.tools = self._create_tools()
        self.agent = initialize_agent(
            self.tools, 
            self.llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True,
            max_iterations=5
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create enhanced tools for the trading agent"""
        return [
            Tool(
                name="Get Portfolio",
                func=self.get_portfolio_analysis,
                description="Get current portfolio balances and analysis"
            ),
            Tool(
                name="Get Market Data",
                func=self.get_market_analysis,
                description="Get current market prices and trends for all tokens"
            ),
            Tool(
                name="Execute Trade",
                func=self.execute_smart_trade,
                description="Execute a trade with risk management. Format: 'from_token,to_token,percentage'"
            ),
            Tool(
                name="Analyze Opportunities",
                func=self.analyze_trading_opportunities,
                description="Analyze current market for trading opportunities"
            ),
            Tool(
                name="Risk Assessment",
                func=self.assess_risk,
                description="Assess portfolio risk and suggest adjustments"
            )
        ]
    
    def get_portfolio_analysis(self, _=None) -> str:
        """Get comprehensive portfolio analysis"""
        try:
            # Get portfolio from Recall API
            portfolio_data = get_portfolio()
            
            if not portfolio_data.get("success"):
                return "❌ Unable to fetch portfolio data. Check your API connection."
            
            total_value = portfolio_data.get("totalValue", 0)
            tokens = portfolio_data.get("tokens", [])
            
            # Create balances dict from portfolio data
            balances = {}
            for token in self.supported_tokens:
                balances[token] = 0.0
                
            for token_data in tokens:
                symbol = token_data.get("symbol", "").upper()
                if symbol in balances:
                    balances[symbol] = float(token_data.get("amount", 0))
            
            if self.initial_portfolio_value is None:
                self.initial_portfolio_value = total_value
            
            performance = ((total_value - self.initial_portfolio_value) / self.initial_portfolio_value * 100) if self.initial_portfolio_value else 0
            
            analysis = f"""
            📊 PORTFOLIO ANALYSIS
            Total Value: ${total_value:.2f}
            Performance: {performance:+.2f}%
            
            Token Balances:
            """
            
            for token, balance in balances.items():
                price = get_token_price(token)
                value = balance * price
                percentage = (value / total_value * 100) if total_value > 0 else 0
                analysis += f"• {token}: {balance:.4f} (${value:.2f}, {percentage:.1f}%)\n"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Portfolio analysis error: {e}")
            return f"❌ Portfolio analysis failed: {e}"
    
    def get_market_analysis(self, _=None) -> str:
        """Get market analysis for all supported tokens"""
        try:
            market_data = {}
            analysis = "📈 MARKET ANALYSIS\n"
            
            for token in self.supported_tokens:
                price = get_token_price(token)
                market_data[token] = price
                analysis += f"• {token}: ${price:.4f}\n"
            
            # Add basic trend analysis
            if "WETH" in market_data and "USDC" in market_data:
                eth_price = market_data["WETH"]
                if eth_price > 2600:
                    analysis += "\n🔴 WETH appears high - consider taking profits\n"
                elif eth_price < 2400:
                    analysis += "\n🟢 WETH appears low - potential buying opportunity\n"
                else:
                    analysis += "\n🟡 WETH in neutral range\n"
            
            # Stablecoin analysis
            if "USDC" in market_data and "DAI" in market_data:
                usdc_price = market_data["USDC"]
                dai_price = market_data["DAI"]
                spread = abs(usdc_price - dai_price) / usdc_price
                
                if spread > 0.003:  # 0.3% spread
                    analysis += f"⚡ Stablecoin arbitrage opportunity detected: {spread*100:.2f}% spread\n"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return f"❌ Market analysis failed: {e}"
    
    def analyze_trading_opportunities(self, _=None) -> str:
        """Analyze current trading opportunities"""
        try:
            opportunities = []
            
            # Get current market data
            prices = {}
            balances = {}
            
            for token in self.supported_tokens:
                prices[token] = get_token_price(token)
                balances[token] = get_balance(token)
            
            # 1. Stablecoin arbitrage
            if balances["USDC"] > self.min_trade_amount:
                usdc_price = prices["USDC"]
                dai_price = prices["DAI"]
                
                if dai_price < usdc_price * 0.997:  # DAI is cheaper
                    opportunities.append({
                        "type": "arbitrage",
                        "action": "Buy DAI with USDC",
                        "confidence": "HIGH",
                        "reason": f"DAI cheaper by {((usdc_price - dai_price) / usdc_price * 100):.3f}%"
                    })
            
            # 2. WETH mean reversion
            weth_price = prices["WETH"]
            if weth_price > 2600 and balances["WETH"] > 0.01:
                opportunities.append({
                    "type": "profit_taking",
                    "action": "Sell WETH to USDC",
                    "confidence": "MEDIUM",
                    "reason": f"WETH high at ${weth_price:.2f}, take profits"
                })
            elif weth_price < 2400 and balances["USDC"] > 100:
                opportunities.append({
                    "type": "value_buying",
                    "action": "Buy WETH with USDC",
                    "confidence": "MEDIUM",
                    "reason": f"WETH low at ${weth_price:.2f}, buying opportunity"
                })
            
            # Format opportunities
            if opportunities:
                result = "🎯 TRADING OPPORTUNITIES:\n"
                for i, opp in enumerate(opportunities, 1):
                    result += f"{i}. {opp['action']} ({opp['confidence']} confidence)\n   Reason: {opp['reason']}\n"
            else:
                result = "😴 No clear trading opportunities detected. Market conditions are neutral."
            
            return result
            
        except Exception as e:
            logger.error(f"Opportunity analysis error: {e}")
            return f"❌ Opportunity analysis failed: {e}"
    
    def assess_risk(self, _=None) -> str:
        """Assess portfolio risk"""
        try:
            balances = {}
            total_value = 0
            
            for token in self.supported_tokens:
                balance = get_balance(token)
                price = get_token_price(token)
                value = balance * price
                balances[token] = value
                total_value += value
            
            risk_assessment = "⚖️ RISK ASSESSMENT:\n"
            
            # Calculate diversification
            if total_value > 0:
                concentrations = {token: (value / total_value) for token, value in balances.items()}
                
                max_concentration = max(concentrations.values())
                if max_concentration > 0.7:
                    risk_assessment += f"🔴 HIGH RISK: Over-concentrated in one asset ({max_concentration*100:.1f}%)\n"
                elif max_concentration > 0.5:
                    risk_assessment += f"🟡 MEDIUM RISK: Moderate concentration ({max_concentration*100:.1f}%)\n"
                else:
                    risk_assessment += f"🟢 LOW RISK: Well diversified (max {max_concentration*100:.1f}%)\n"
                
                # Stablecoin exposure
                stable_exposure = concentrations.get("USDC", 0) + concentrations.get("DAI", 0)
                risk_assessment += f"💰 Stablecoin exposure: {stable_exposure*100:.1f}%\n"
                
                # Volatile asset exposure
                volatile_exposure = concentrations.get("WETH", 0)
                risk_assessment += f"📈 Volatile asset exposure: {volatile_exposure*100:.1f}%\n"
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return f"❌ Risk assessment failed: {e}"
    
    def execute_smart_trade(self, trade_params: str) -> str:
        """Execute trade with enhanced risk management"""
        try:
            # Parse parameters: "from_token,to_token,percentage"
            params = trade_params.split(",")
            if len(params) != 3:
                return "❌ Invalid format. Use: 'from_token,to_token,percentage'"
            
            from_token, to_token, percentage_str = [p.strip() for p in params]
            percentage = float(percentage_str)
            
            # Validate tokens
            if from_token not in self.supported_tokens or to_token not in self.supported_tokens:
                return f"❌ Unsupported token. Supported: {self.supported_tokens}"
            
            # Validate percentage
            if percentage <= 0 or percentage > self.max_trade_percentage * 100:
                return f"❌ Invalid percentage. Must be 0-{self.max_trade_percentage*100}%"
            
            # Get current balance
            from_balance = get_balance(from_token)
            trade_amount = from_balance * (percentage / 100)
            
            if trade_amount < self.min_trade_amount:
                return f"❌ Trade amount too small: {trade_amount:.4f} {from_token}"

           # Generate a degen/Vadar-style reason for the trade
            reason_prompt = f"Generate a short Darth Vadar-style reason to swap {trade_amount:.2f} {from_token} to {to_token}"
            reason = self.llm.invoke(reason_prompt).strip()
            logger.info(f"📝 Trade Reason: {reason}")
            
            # Execute trade
            logger.info(f"Executing trade: {trade_amount:.4f} {from_token} -> {to_token}")
            result = perform_swap(from_token, to_token, trade_amount, "evm", reason=reason)
            
            # Log trade
            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "from_token": from_token,
                "to_token": to_token,
                "amount": trade_amount,
                "percentage": percentage,
                "reason": reason,
                "result": result
            }
            self.trade_history.append(trade_record)
            
            return f"✅ Trade executed: {trade_amount:.4f} {from_token} -> {to_token}\nReason: {reason}\nResult: {result}"
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return f"❌ Trade execution failed: {e}"
    
    def run_trading_cycle(self) -> str:
        """Run one complete trading cycle"""
        try:
            logger.info("🤖 Starting trading cycle...")
            
            # Create comprehensive prompt for the agent
            prompt = """
            You are an autonomous trading agent. Analyze the current market conditions and portfolio,
            then decide on the best trading action. Consider:
            
            1. Portfolio diversification and risk management
            2. Market opportunities (arbitrage, mean reversion)
            3. Profit-taking and loss prevention
            4. Overall portfolio performance
            
            Use the available tools to gather information and make an informed decision.
            If you decide to trade, use the Execute Trade tool with format: 'from_token,to_token,percentage'
            
            Be conservative and prioritize capital preservation.
            """
            
            response = self.agent.run(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Trading cycle error: {e}")
            return f"❌ Trading cycle failed: {e}"
    
    def run_autonomous_loop(self, interval_minutes: int = 30):
        """Run the autonomous trading loop"""
        logger.info(f"🚀 Starting autonomous trading agent (interval: {interval_minutes} minutes)")
        
        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                logger.info(f"\n{'='*50}")
                logger.info(f"🔄 Trading Cycle #{cycle_count}")
                logger.info(f"{'='*50}")
                
                # Run trading cycle
                result = self.run_trading_cycle()
                logger.info(f"Cycle result: {result}")
                
                # Wait for next cycle
                wait_seconds = interval_minutes * 60
                logger.info(f"⏱️ Waiting {interval_minutes} minutes until next cycle...")
                time.sleep(wait_seconds)
                
            except KeyboardInterrupt:
                logger.info("🛑 Trading bot stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in trading loop: {e}")
                logger.info("⏱️ Waiting 5 minutes before retry...")
                time.sleep(300)  # Wait 5 minutes on error

def main():
    """Main function to start the enhanced trading agent"""
    try:
        # Validate environment variables
        required_vars = ["GROQ_API_KEY", "RECALL_API_KEY", "RECALL_API_URL"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing environment variables: {missing_vars}")
            return
        
        # Create and run the trading agent
        agent = EnhancedTradingAgent()
        
        # Option to run a single cycle for testing
        if os.getenv("TEST_MODE", "").lower() == "true":
            logger.info("🧪 Running in test mode (single cycle)")
            result = agent.run_trading_cycle()
            logger.info(f"Test result: {result}")
        else:
            # Run continuous autonomous loop
            interval = int(os.getenv("TRADING_INTERVAL_MINUTES", "30"))
            agent.run_autonomous_loop(interval)
            
    except Exception as e:
        logger.error(f"❌ Failed to start trading agent: {e}")

if __name__ == "__main__":
    main()
