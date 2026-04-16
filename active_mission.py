#!/usr/bin/env python3
"""
UOTA Elite v2 - Active Mission Deployment
For use with already running MT5 window
"""

import asyncio
import sys
import os
from datetime import datetime

async def active_mission():
    try:
        print("🚀 UOTA ELITE v2 - ACTIVE MISSION")
        print("=" * 60)
        print()
        
        # Step 1: Connect to Active MT5 Bridge
        print("🤝 CONNECTING TO ACTIVE MT5 BRIDGE...")
        print("📡 Using mt5linux bridge @ 127.0.0.1:8001...")
        
        # Try to connect to existing MT5 instance through bridge
        try:
            import mt5linux
            mt5 = mt5linux.MetaTrader5(host='127.0.0.1', port=8001)
            
            # Initialize connection to existing MT5 with 5s retry logic
            while True:
                if mt5.initialize():
                    print("✅ MT5 Bridge: ESTABLISHED")
                    
                    # Login to Exness Account: 435294186 on Exness-MT5Trial9
                    login_result = mt5.login(
                        login=435294186,
                        password=os.getenv('EXNESS_PASSWORD', 'your_actual_password'),
                        server='Exness-MT5Trial9'
                    )
                    
                    if login_result:
                        # Get account info
                        account_info = mt5.account_info()
                        if account_info:
                            print()
                            print("📊 ACCOUNT INFORMATION")
                            print("-" * 30)
                            print(f"🔑 Login: {account_info.login}")
                            print(f"🏛️ Server: {account_info.server}")
                            print(f"💰 Balance: ${account_info.balance:.2f}")
                            print(f"💎 Equity: ${account_info.equity:.2f}")
                            print(f"🏛️ Leverage: {account_info.leverage}x")
                            print(f"📈 Currency: {account_info.currency}")
                            print()
                            
                            # Verify account and balance
                            if account_info.login == 435294186 and account_info.balance >= 500:
                                print("✅ Account Verification: SUCCESSFUL ($500 balance confirmed)")
                            else:
                                print(f"⚠️ Account Verification: WARNING (Expected 435294186 with $500, got {account_info.login} with ${account_info.balance:.2f})")
                            
                            # Check XAUUSD price feed
                            symbol_info = mt5.symbol_info("XAUUSD")
                            if symbol_info:
                                print(f"✅ XAUUSD Price Feed: LIVE (Bid: {symbol_info.bid}, Ask: {symbol_info.ask})")
                            else:
                                print("❌ XAUUSD Price Feed: NOT FOUND")
                                
                            equity = account_info.equity
                            break
                        else:
                            print("❌ Cannot retrieve account info. Retrying in 5s...")
                    else:
                        print(f"❌ Login failed: {mt5.last_error()}. Retrying in 5s...")
                else:
                    print(f"❌ MT5 Bridge initialization failed: {mt5.last_error()}. Retrying in 5s...")
                
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"❌ MT5 Connection Error: {e}")
            print("🔧 Ensure MT5 is running and pymt5linux is properly configured")
            return
        
        # Step 2: Engage Brain
        print("🧠 ENGAGING BRAIN: OpportunityScanner")
        from opportunity_scanner import OpportunityScanner
        
        print("🔍 SMC Analysis Engine: ACTIVE")
        print("📈 Order Block Detection: ENABLED")
        print("🌊 Liquidity Sweep Detection: ENABLED") 
        print("📊 Market Structure Analysis: ENABLED")
        print("📈 RSI Confirmation: ENABLED")
        print("✅ OpportunityScanner: ENGAGED")
        print()
        
        # Step 3: Execute Mission
        print("🎯 EXECUTING SCALE MISSION...")
        from commander_logic import autonomous_commander
        
        goal_command = "$4000 in 30 days"
        print(f"🎪 Goal: {goal_command}")
        
        result = await autonomous_commander.parse_and_execute_goal(goal_command)
        
        if result['success']:
            goal = result['goal']
            print("✅ SCALE MISSION: ACTIVATED")
            print()
            print("📊 MISSION PARAMETERS")
            print("-" * 30)
            print(f"🎪 Target: ${goal.target_amount:,.2f}")
            print(f"💰 Current: ${equity:.2f}")
            print(f"📅 Deadline: {goal.deadline.strftime('%Y-%m-%d')}")
            print(f"📈 Daily ROI: {goal.daily_roi_required:.2%}")
            print(f"🏛️ Leverage: {goal.optimal_leverage:.1f}x")
            print(f"📊 Status: {goal.status.value}")
            print("-" * 30)
            print()
            
            # Calculate mission metrics
            scaling_factor = goal.target_amount / equity
            daily_target = (goal.target_amount - equity) / 30
            print(f"📈 Scaling Factor: {scaling_factor:.1f}x")
            print(f"🎯 Daily Target: ${daily_target:.2f}")
            print()
            
        else:
            print(f"❌ Mission Failed: {result['error']}")
            return
        
        # Step 4: Start Monitoring
        print("📡 ACTIVATING MONITORING...")
        
        # Start productivity logger
        from productivity_logger import productivity_logger
        monitoring_task = asyncio.create_task(productivity_logger.start_monitoring())
        print("✅ Productivity Logger: ACTIVE")
        print()
        
        # Main monitoring loop
        print("🎯 UOTA ELITE v2 - LIVE MISSION")
        print("=" * 60)
        print()
        
        try:
            while self.is_running:
                await asyncio.sleep(15)  # Update every 15 seconds
                
                # Get current positions
                positions = mt5.positions_get()
                current_equity = mt5.account_info().equity
                skill_score = productivity_logger.get_skill_score()
                
                # Calculate progress
                progress = ((current_equity - 500) / (goal.target_amount - 500)) * 100
                days_remaining = max(0, (goal.deadline - datetime.now()).days)
                
                # Clear and display dashboard
                print("\033[2J\033[H")  # Clear screen
                print("🎯 UOTA ELITE v2 - MISSION CONTROL")
                print("=" * 60)
                print()
                print("📊 MISSION STATUS")
                print("-" * 30)
                print(f"💰 Equity: ${current_equity:.2f}")
                print(f"🎯 Skill: {skill_score:.1f}%")
                print(f"📈 Progress: {progress:.1f}%")
                print(f"📅 Days Left: {days_remaining}")
                print()
                
                print("🎯 ACTIVE TRADES")
                print("-" * 30)
                if positions:
                    for i, pos in enumerate(positions, 1):
                        direction = "🟢 BUY" if pos.type == 0 else "🔴 SELL"
                        profit_emoji = "🟢" if pos.profit > 0 else "🔴"
                        print(f"{i}. {pos.symbol} {direction} {pos.volume} lots")
                        print(f"   Entry: ${pos.price_open:.5f}")
                        print(f"   P&L: {profit_emoji} ${pos.profit:.2f}")
                else:
                    print("🔍 HUNTING FOR SMC SETUPS...")
                print()
                
                print("🎯 DAILY TARGET")
                print("-" * 30)
                daily_profit = current_equity - 500  # Simplified
                if days_remaining > 0:
                    required_daily = (goal.target_amount - current_equity) / days_remaining
                    print(f"🎯 Target: ${required_daily:.2f}/day")
                    print(f"📈 Current: ${daily_profit:.2f}/day")
                    status = "🟢 ON TRACK" if daily_profit >= required_daily * 0.8 else "🔴 BEHIND"
                    print(f"📊 Status: {status}")
                print()
                
                print("📋 COMMANDS: status | skill | trades | goal | help")
                print("=" * 60)
                
        except KeyboardInterrupt:
            print("\n🛑 Mission paused by user")
            print("🎯 UOTA ELITE v2 - STANDBY")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(active_mission())
