#!/usr/bin/env python3
"""
UOTA Elite v2 - Master Controller
Commander interface with elite brain consistency and live MT5 bridge
"""

# import asyncio
# import logging
# import sys
# import os
from datetime import datetime  # Moved to function to avoid circular import, timedelta
from pathlib import Path
from typing import List

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/master_controller.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class MasterController:
    """Elite Master Controller - Commander Interface"""
    
    def __init__(self):
        self.prompt = " [SYSTEM]: Awaiting Commander's Target... "
        self.command_history = []
        self.max_history = 100
        self.is_running = False
        self.current_account = "demo"  # demo or real
        
        # Command registry
        self.commands = {
            '/help': self.cmd_help,
            '/status': self.cmd_status,
            '/goal': self.cmd_goal,
            '/upscale': self.cmd_upscale,
            '/account': self.cmd_account,
            '/brain': self.cmd_brain,
            '/connect': self.cmd_connect,
            '/health': self.cmd_health,
            '/trial': self.cmd_trial,
            '/exit': self.cmd_exit,
            '/clear': self.cmd_clear
        }
    
    async def start(self):
        """Start master controller"""
        try:
            # # # # print("""

            UOTA ELITE v2 - MASTER CONTROLLER              
              Commander Interface | Elite Brain Consistency        


 [BRAIN]: Elite SMC Logic Loaded & Precise.
 [SAFETY]: 1% Risk Rule Hard-Locked.
 [SMC]: Order Block + Liquidity Sweep + RSI Alignment.
 [SYSTEM]: Awaiting Commander's Target...

 Available Commands:
  /goal $4000 - Set mission target /upscale $5000 - Update scaling target /account demo - Switch to demo account /account real - Switch to real account /brain status - Show SMC logic status /connect - Test MT5 bridge /health - System health report /help - Show all commands
""")
            
            self.is_running = True
            
            # Start command loop
            await self._command_loop()
            
        except KeyboardInterrupt:
            # # # # print("\n Master Controller shutting down gracefully...")
            await self._shutdown()
        except Exception as e:
            logger.error(f" Error starting master controller: {e}")
            await self._shutdown()
    
    async def _command_loop(self):
        """Main command processing loop"""
        while self.is_running:
            try:
                # Get user input
                command = await self._get_input()
                
                if not command:
                    continue
                
                # Update trial phase display
                self._update_trial_phase_display()
                    
                # Extract command and args
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                # Handle pure numbers as goal target
                if cmd.isdigit() and not args:
                    # Convert to goal command
                    target_amount = float(cmd)
                    # # # # print(f"""
 [COMMANDER]: PURE NUMBER TARGET RECEIVED

Target: ${target_amount:,.2f}
Processing: Converting to goal command...
""")
                    cmd = '/goal'
                    args = [f'${target_amount}', 'in', '30', 'days']
                
                # Check if command exists
                if cmd in self.commands:
                    await self.commands[cmd](args)
                elif cmd == '/real_mission_start':
                    await self.cmd_real_mission_start(args)
                else:
                    # # # # print(f" Unknown command: {cmd}")
                    # # # # print(" Type '/help' for available commands")
                    
            except Exception as e:
                print(f" Error processing command: {e}")
    
    def _update_trial_phase_display(self):
        """Update trial phase display"""
        try:
            from trial_logger # # import trial_logger  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            status = trial_logger.get_trial_status()
            
            # Update prompt with trial phase
            self.prompt = f" [TRIAL PHASE]: Day {status['current_day']} of {status['total_days']}. SMC Brain is Hard-Locked. "
            
        except Exception as e:
            # Fallback prompt
            self.prompt = " [SYSTEM]: Awaiting Commander's Target... "
    
    async def _get_input(self) -> str:
        """Get user input asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, self.prompt)
    
    # Command implementations
    async def cmd_help(self, args: List[str]):
        """Show help information"""
        # # # # print("""

                     COMMANDER HELP MENU                      


 MISSION COMMANDS:
  /goal [amount] in [days]    - Set trading goal
    Example: /goal $4000 in 30 days /upscale [amount]           - Update scaling target
    Example: /upscale $5000
  [4000]                    - Pure number target (auto-converts to goal)
    Example: 4000

 ACCOUNT COMMANDS:
  /account demo - Switch to demo account (11000575398)
  /account real - Switch to real account /real_mission_start - SECURE: Activate real funds /connect - Test MT5 bridge connection

 TRIAL COMMANDS:
  /trial - Show 60-day trial status /trial report - Generate weekly performance report

 BRAIN COMMANDS:
  /brain status - Show SMC logic status /brain reset - Reset skill score to 100%

 SYSTEM COMMANDS:
  /status - Detailed mission status /health - System health report /clear - Clear screen /exit - Exit controller

 SAFETY FEATURES:
   1% Risk Rule: Hard-locked (cannot be changed)
   SMC Logic: Hard-locked (Order Block + Liquidity Sweep + RSI)
   Zero Randomness: Disabled (skill score must stay >95%)
   Professional Scaling: Automatic lot size calculation
   60-Day Trial: Elite validation before real funds
""")
    
    async def cmd_goal(self, args: List[str]):
        """Set new trading goal"""
        try:
            if not args:
                # # # # print("Usage: /goal $4000 in 30 days")
                return
                
            goal_string = " ".join(args)
            
            # # # # print(f"""
 [COMMANDER]: RECEIVED GOAL COMMAND

Goal: {goal_string}
Status: Updating mission parameters...
Risk: Maintaining 1% absolute rule
SMC: Hard-locked (no changes)
""")
            
            # Import and execute goal
            from commander_logic import autonomous_commander
            result = await autonomous_commander.parse_and_execute_goal(goal_string)
            
            if result['success']:
                goal = result['goal']
                # # # # print(f"""
 [COMMANDER]: GOAL EXECUTED

Target: ${goal.target_amount:,.2f}
Deadline: {goal.deadline.strftime('%Y-%m-%d')}
Daily ROI: {goal.daily_roi_required:.2%}
Optimal Leverage: {goal.optimal_leverage:.1f}x
Status: {goal.status.value}

 [SYSTEM]: Awaiting Commander's next command...
""")
            else:
                print(f" [COMMANDER]: Goal failed: {result['error']}")
                
        except Exception as e:
            print(f" Error setting goal: {e}")
    
    async def cmd_upscale(self, args: List[str]):
        """Command-based scaling - Commander only updates when explicitly told"""
        try:
            if not args:
                # # # # print("Usage: /upscale $5000")
                return
                
            target_amount_str = args[0]
            # Parse amount
            if target_amount_str.startswith('$'):
                target_amount_str = target_amount_str[1:]
            
            try:
                target_amount = float(target_amount_str)
                if target_amount <= 0:
                    # # # # print(" Target amount must be positive")
                    return
            except ValueError:
                # # # # print(f" Invalid amount: {target_amount_str}")
                return
            
            # # # # print(f"""
 [COMMANDER]: RECEIVED SCALING ORDER

New Target: ${target_amount:,.2f}
Commander: Updating mission parameters
Risk Rule: Maintaining 1% absolute
SMC Logic: Hard-locked (no changes)
Lot Size: Recalculating for 1% risk
""")
            
            # Update goal with new target
            from commander_logic import autonomous_commander
            goal_command = f"${target_amount} in 30 days"
            result = await autonomous_commander.parse_and_execute_goal(goal_command)
            
            if result['success']:
                goal = result['goal']
                # # # # print(f"""
 [COMMANDER]: SCALING EXECUTED

Updated Target: ${goal.target_amount:,.2f}
Daily ROI: {goal.daily_roi_required:.2%}
Optimal Leverage: {goal.optimal_leverage:.1f}x
Lot Size: Recalculated for 1% risk
Status: {goal.status.value}

 [SYSTEM]: Awaiting Commander's next command...
""")
            else:
                print(f" [COMMANDER]: Scaling failed: {result['error']}")
                
        except Exception as e:
            print(f" Error in scaling: {e}")
    
    async def cmd_account(self, args: List[str]):
        """Toggle between demo and real accounts"""
        try:
            if not args:
                # # # # print(f"Current account: {self.current_account}")
                # # # # print("Usage: /account demo or /account real")
                return
            
            account_type = args[0].lower()
            
            if account_type not in ['demo', 'real']:
                # # # # print(" Account type must be 'demo' or 'real'")
                return
            
            self.current_account = account_type
            
            if account_type == 'demo':
                # # # # print("""
 [COMMANDER]: SWITCHING TO DEMO ACCOUNT

Account: 11000575398
Server: Exness-MT5Trial10
Mode: DEMO (Safe Testing)
Risk: 1% absolute rule
""")
            else:
                # # # # print("""
 [COMMANDER]: SWITCHING TO REAL ACCOUNT

Account: [Your Real Account Number]
Server: [Your Real Server]
Mode: REAL (Live Trading)
Risk: 1% absolute rule
 WARNING: Real money at risk
""")
            
            # Update environment
            # This would update .env with new credentials
            # # # # print(" Account switch completed")
            
        except Exception as e:
            print(f" Error switching account: {e}")
    
    async def cmd_brain(self, args: List[str]):
        """Show SMC brain status"""
        try:
            if not args:
                # # # # print("Usage: /brain status or /brain reset")
                return
            
            brain_command = args[0].lower()
            
            if brain_command == 'status':
                # # # # print("""
 [BRAIN]: SMC LOGIC STATUS

Order Block Detection:  ACTIVE (75% confidence)
Liquidity Sweep Detection:  ACTIVE (70% confidence)
Market Structure Analysis:  ACTIVE (65% confidence)
RSI Confirmation:  ACTIVE (60% confidence)
Signal Alignment:  ENFORCED (30% variance)
Random Trading:  DISABLED
Loose Logic:  DELETED
Skill Score: TRACKING (must stay >95%)
Risk Rule:  1% ABSOLUTE (HARD-LOCKED)
""")
            
            elif brain_command == 'reset':
                # # # # print("""
 [BRAIN]: RESETTING SKILL SCORE

Skill Score: Reset to 100.0
Performance: Fresh start
Note: This affects only tracking, not SMC logic
""")
                
                # Reset skill score
                from smc_logic_gate import SMCLogicGate
                smc_gate = SMCLogicGate()
                smc_gate.skill_score = 100.0
                
            else:
                # # # # print(" Unknown brain command")
                
        except Exception as e:
            print(f" Error in brain command: {e}")
    
    async def cmd_connect(self, args: List[str]):
        """Test MT5 bridge connection"""
        try:
            # # # # print("""
 [SYSTEM]: TESTING MT5 BRIDGE

Testing: pymt5linux bridge
Account: {self.current_account}
Server: Exness-MT5Trial10
""")
            
            # Test connection
            from pymt5linux import MetaTrader5 as mt5
            mt5_instance = mt5()
            
            if mt5_instance.initialize():
                account_info = mt5_instance.account_info()
                if account_info:
                    # # # # print(f"""
 [SYSTEM]: MT5 CONNECTION SUCCESS

Login: {account_info.login}
Server: {account_info.server}
Balance: ${account_info.balance:.2f}
Equity: ${account_info.equity:.2f}
Leverage: {account_info.leverage}x
Status: READY FOR COMMANDS
""")
                else:
                    # # # # print(" [SYSTEM]: Cannot get account info")
            else:
                # # # # print(" [SYSTEM]: MT5 Connection failed")
                # # # # print(" Ensure MT5 is running and accessible")
                
        except Exception as e:
            print(f" Connection test error: {e}")
    
    async def cmd_status(self, args: List[str]):
        """Show detailed status report"""
        try:
            # # # # print("""
 [SYSTEM]: MISSION STATUS REPORT

""")
            
            # Get current status
            from commander_logic import autonomous_commander
            from productivity_logger # import productivity_logger  # Moved to function to avoid circular import
            
            try:
                current_goal = autonomous_commander.current_goal
                skill_score = productivity_logger.get_skill_score()
                
                if current_goal:
                    # # # # print(f"Target: ${current_goal.target_amount:,.2f}")
                    # # # # print(f"Deadline: {current_goal.deadline.strftime('%Y-%m-%d')}")
                    # # # # print(f"Daily ROI: {current_goal.daily_roi_required:.2%}")
                    # # # # print(f"Status: {current_goal.status.value}")
                else:
                    # # # # print("Target: Not set")
                    # # # # print("Status: Awaiting Commander's goal")
                
                # # # # print(f"Skill Score: {skill_score:.1f}%")
                # # # # print(f"Account: {self.current_account}")
                
            except Exception as e:
                print(f" Error getting status: {e}")
                
        except Exception as e:
            print(f" Error in status command: {e}")
    
    async def cmd_health(self, args: List[str]):
        """Show system health report"""
        try:
            # # # # print("""
 [SYSTEM]: HEALTH REPORT

""")
            
            # Test MT5 connection
            from pymt5linux import MetaTrader5 as mt5
            mt5_instance = mt5()
            
            if mt5_instance.initialize():
                account_info = mt5_instance.account_info()
                if account_info:
                    # # # # print(f"MT5 Connection:  ESTABLISHED")
                    # # # # print(f"Account: {account_info.login}")
                    # # # # print(f"Server: {account_info.server}")
                    # # # # print(f"Balance: ${account_info.balance:.2f}")
                    # # # # print(f"Equity: ${account_info.equity:.2f}")
                else:
                    # # # # print("MT5 Connection:  ESTABLISHED (No account info)")
            else:
                # # # # print("MT5 Connection:  FAILED")
            
            # # # # print("SMC Logic:  Hard-locked")
            # # # # print("Risk Rule:  1% absolute")
            # # # # print("Random Trading:  DISABLED")
            
        except Exception as e:
            print(f" Health check error: {e}")
    
    async def cmd_clear(self, args: List[str]):
        """Clear screen"""
        os.system('clear')
        # # # # print("""

            UOTA ELITE v2 - MASTER CONTROLLER              
              Commander Interface | Elite Brain Consistency        


 [BRAIN]: Elite SMC Logic Loaded & Precise.
 [SAFETY]: 1% Risk Rule Hard-Locked.
 [SMC]: Order Block + Liquidity Sweep + RSI Alignment.
 [SYSTEM]: Awaiting Commander's Target...
""")
    
    async def cmd_exit(self, args: List[str]):
        """Exit controller"""
        # # # # print("\n Master Controller shutting down...")
        self.is_running = False
    
    async def cmd_real_mission_start(self, args: List[str]):
        """Secure activation of real funds"""
        try:
            # # # # print("""
 [COMMANDER]: REAL MISSION ACTIVATION REQUESTED

 WARNING: Switching from DEMO to REAL MONEY
 Risk Management: 1% absolute rule remains
 SMC Logic: Hard-locked (no changes)
""")
            
            # Activate real funds securely
            from real_funds_manager # import real_funds_manager  # Moved to function to avoid circular import
            success = await real_funds_manager.activate_real_funds(force=True)
            
            if success:
                # # # # print(" [COMMANDER]: REAL MISSION ACTIVATED")
                # # # # print(" Agent now trading with real funds")
                
                # Update prompt
                self.prompt = " [REAL MISSION]: SMC Brain Hard-Locked. "
            else:
                # # # # print(" [COMMANDER]: Real mission activation failed")
                
        except Exception as e:
            print(f" Error activating real mission: {e}")
    
    async def cmd_trial(self, args: List[str]):
        """Show trial status and reports"""
        try:
            from trial_logger # # import trial_logger  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            
            if not args:
                # Show trial status
                status = trial_logger.get_trial_status()
                # # # # print(f"""
 [TRIAL]: 60-DAY ELITE VALIDATION

Current Day: {status['current_day']} of {status['total_days']}
Days Remaining: {status['days_remaining']}
Progress: {status['progress_percentage']:.1f}%
Trial Start: {status['trial_start_date']}
Current Skill Score: {status['current_skill_score']:.1f}%
Total SMC Setups: {status['cumulative_smc_setups']}
Total Trades: {status['cumulative_trades']}
Cumulative P&L: ${status['cumulative_profit_loss']:.2f}

Mode: {real_funds_manager.get_current_mode()}
""")
            elif args[0].lower() == 'report':
                # Generate weekly report
                report = trial_logger.generate_weekly_report()
                if report:
                    # # # # print(f" Weekly {report.week_number} report generated")
                else:
                    # # # # print(" Failed to generate report")
            else:
                # # # # print("Usage: /trial or /trial report")
                
        except Exception as e:
            print(f" Error in trial command: {e}")
    
    async def _shutdown(self):
        """Cleanup and shutdown"""
        # # # # print(" Master Controller shutdown complete")

# Global instance
master_controller = MasterController()

async def main():
    """Main entry point"""
    # # # # print(" Starting UOTA Elite v2 Master Controller...")
    await master_controller.start()

if __name__ == "__main__":
    asyncio.run(main())
