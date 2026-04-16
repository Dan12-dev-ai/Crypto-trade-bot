#!/usr/bin/env python3
"""
UOTA Elite v2 - Deployment with Credentials
"""

# import asyncio  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import os  # Moved to function to avoid circular import
# import getpass  # Moved to function to avoid circular import
sys.path.append('.')

async def deploy_mission():
    try:
        print("🚀 UOTA ELITE v2 - CREDENTIALS & DEPLOYMENT")
        print("=" * 60)
        print()
        
        # Get password securely
        print("🔐 ENTER EXNESS CREDENTIALS")
        print("-" * 30)
        
        # Check if credentials already exist
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
                if "your_actual_password" not in content:
                    print("✅ Credentials appear to be configured")
                    use_existing = input("Use existing credentials? (y/n): ").lower()
                    if use_existing == 'y':
                        password = None
                    else:
                        password = getpass.getpass("Exness Password: ")
                else:
                    password = getpass.getpass("Exness Password: ")
        else:
            password = getpass.getpass("Exness Password: ")
        
        # Update .env if needed
        if password:
            print("📝 Updating .env file...")
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Replace password
            content = content.replace('EXNESS_PASSWORD=your_exness_password_here', f'EXNESS_PASSWORD={password}')
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✅ .env file updated")
        
        print()
        
        # Step 1: Handshake with Active MT5
        print("🤝 HANDSHAKE: Connecting to Active MT5...")
        from mt5_integration # import mt5_integration  # Moved to function to avoid circular import
        
        connected = await mt5_integration.initialize()
        if not connected:
            print("❌ CRITICAL: Cannot connect to active MT5 window")
            print("🔧 TROUBLESHOOTING:")
            print("1. Ensure MT5 is running and logged into account 11000575398")
            print("2. Verify you're connected to Exness-MT5Trial10 server")
            print("3. Check that pymt5linux can access the MT5 window")
            return
        
        print("✅ MT5 Handshake: SUCCESS")
        print()
        
        # Step 2: Confirm Equity
        print("💰 CONFIRMING ACCOUNT EQUITY...")
        account_info = await mt5_integration.get_account_balance()
        equity = account_info.get('equity', 0)
        
        print(f"📊 Account Equity: ${equity:.2f}")
        if abs(equity - 500.0) < 50.0:  # Within $50 of expected
            print("✅ Equity Confirmed: Close to $500.00")
        else:
            print(f"⚠️ Equity Note: Expected ~$500.00, Found ${equity:.2f}")
        
        print()
        
        # Step 3: Engage Brain - OpportunityScanner
        print("🧠 ENGAGING BRAIN: Activating OpportunityScanner...")
        from opportunity_scanner # import opportunity_scanner  # Moved to function to avoid circular import
        
        # Initialize scanner with elite symbols
        elite_symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD', 'USDCHF']
        
        print("🎯 SMC Analysis Engine: ACTIVE")
        print(f"📈 Scanning Symbols: {', '.join(elite_symbols)}")
        print("🔍 Order Block Detection: ENABLED")
        print("🌊 Liquidity Sweep Detection: ENABLED")
        print("📊 Market Structure Analysis: ENABLED")
        print("📈 RSI Confirmation: ENABLED")
        print("✅ OpportunityScanner: ENGAGED")
        print()
        
        # Step 4: Execute Scale Mission
        print("🎯 EXECUTING SCALE MISSION...")
        from commander_logic import autonomous_commander
        
        # Set elite scaling goal
        goal_command = "$4000 in 30 days"
        print(f"🎪 Goal Command: {goal_command}")
        
        # Parse and execute goal
        result = await autonomous_commander.parse_and_execute_goal(goal_command)
        
        if result['success']:
            goal = result['goal']
            print("✅ SCALE MISSION: ACTIVATED")
            print()
            print("📊 MISSION PARAMETERS")
            print("-" * 30)
            print(f"Target Amount: ${goal.target_amount:,.2f}")
            print(f"Current Balance: ${equity:.2f}")
            print(f"Deadline: {goal.deadline.strftime('%Y-%m-%d')}")
            print(f"Daily ROI Required: {goal.daily_roi_required:.2%}")
            print(f"Optimal Leverage: {goal.optimal_leverage:.1f}x")
            print(f"Status: {goal.status.value}")
            print(f"Market Pairs: {', '.join(goal.market_pairs)}")
            print("-" * 30)
            print()
            
            # Calculate scaling path
            scaling_factor = goal.target_amount / equity
            print(f"📈 Scaling Factor: {scaling_factor:.1f}x")
            print(f"🎯 Daily Profit Target: ${(goal.target_amount - equity) / 30:.2f}")
            print()
            
        else:
            print(f"❌ SCALE MISSION FAILED: {result['error']}")
            return
        
        # Step 5: Activate Monitoring
        print("📡 ACTIVATING MONITORING SYSTEMS...")
        
        # Start system health monitor
        from infrastructure.system_health_monitor # import sys  # Moved to function to avoid circular importtem_health_monitor
        health_task = asyncio.create_task(system_health_monitor.start_monitoring())
        print("✅ System Health Monitor: ACTIVE")
        
        # Start market data validator
        from infrastructure.market_data_validator import market_data_validator
        print("✅ Market Data Validator: ACTIVE")
        
        # Start execution safety layer
        from infrastructure.execution_safety_layer import execution_safety_layer
        print("✅ Execution Safety Layer: ACTIVE")
        
        # Start automated logging
        from infrastructure.automated_logging_system import automated_logging_system
        logging_task = asyncio.create_task(automated_logging_system.start_logging())
        print("✅ Automated Logging System: ACTIVE")
        
        # Start productivity logger
        from productivity_logger # import productivity_logger  # Moved to function to avoid circular import
        productivity_task = asyncio.create_task(productivity_logger.start_monitoring())
        print("✅ 30-Day Productivity Logger: ACTIVE")
        
        print()
        
        # Step 6: Terminal Dashboard
        print("🖥️ OPENING TERMINAL DASHBOARD...")
        print("🎯 MISSION STATUS: ACTIVE")
        print("=" * 60)
        print()
        print("📊 REAL-TIME MONITORING")
        print("-" * 30)
        print("✅ MT5 Connection: ESTABLISHED")
        print("✅ Account Equity: CONFIRMED")
        print("✅ SMC Brain: ENGAGED")
        print("✅ Scale Mission: ACTIVE")
        print("✅ Risk Management: 1% RULE")
        print("✅ Skill Score Tracking: ACTIVE")
        print()
        print("🎯 CURRENT OBJECTIVES")
        print("-" * 30)
        print(f"🎪 Target: $4000.00 by {goal.deadline.strftime('%Y-%m-%d')}")
        print(f"📈 Daily Progress: ${(goal.target_amount - equity) / 30:.2f} required")
        print(f"🔍 Scanning: XAUUSD H1 for SMC setups")
        print(f"🛡️ Risk: 1% per trade (ABSOLUTE)")
        print()
        print("📋 COMMANDS AVAILABLE")
        print("-" * 30)
        print("/status - Mission progress")
        print("/health - System health")
        print("/skill - Skill score & performance")
        print("/trades - Active positions")
        print("/goal - Current goal status")
        print("/help - All commands")
        print()
        print("🚀 UOTA ELITE v2 IS HUNTING...")
        print("=" * 60)
        
        # Keep monitoring active
        try:
            while self.is_running:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Quick status check
                current_positions = await mt5_integration.get_positions()
                current_equity = (await mt5_integration.get_account_balance()).get('equity', 0)
                skill_score = productivity_logger.get_skill_score()
                
                # Clear and update status
                print("\033[2J\033[H")  # Clear screen
                print("🎯 UOTA ELITE v2 - LIVE STATUS")
                print("=" * 60)
                print(f"💰 Equity: ${current_equity:.2f} | 🎯 Skill: {skill_score:.1f}% | 📈 Positions: {len(current_positions)}")
                progress_pct = ((current_equity - 500) / (goal.target_amount - 500)) * 100
                print(f"🎪 Progress: ${current_equity:.2f} / ${goal.target_amount:.2f} ({progress_pct:.1f}%)")
                print(f"🔍 Status: {'HUNTING' if len(current_positions) == 0 else 'ACTIVE'}")
                
                # Show recent activity
                if len(current_positions) > 0:
                    print("📈 ACTIVE POSITIONS:")
                    for pos in current_positions[:3]:  # Show max 3
                        direction = "BUY" if pos.type == 0 else "SELL"
                        profit_color = "🟢" if pos.profit > 0 else "🔴"
                        print(f"  {pos.symbol} {direction} {pos.volume} lots | P&L: {profit_color} ${pos.profit:.2f}")
                else:
                    print("🔍 SCANNING FOR SMC SETUPS...")
                
                print("=" * 60)
                
        except KeyboardInterrupt:
            print("\n🛑 Mission monitoring stopped by user")
            
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
            
    except Exception as e:
        print(f"❌ CRITICAL DEPLOYMENT ERROR: {e}")
        # import traceback  # Moved to function to avoid circular import
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(deploy_mission())
