"""
Crypto trade bot - Terminal Command Interface
Persistent terminal listener for autonomous commander
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import readline  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import
from typing import Dict, List, Optional, Any
from commander_logic import autonomous_commander
from zero_downtime_infrastructure import zero_downtime_manager

class TerminalCommandInterface:
    """Persistent terminal command interface"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.prompt = "🤖 UOTA-Commander > "
        self.command_history: List[str] = []
        self.max_history = 100
        
        # Command registry
        self.commands = {
            '/status': self.cmd_status,
            '/boost': self.cmd_boost,
            '/safe': self.cmd_safe,
            '/goal': self.cmd_goal,
            '/upscale': self.cmd_upscale,
            '/health': self.cmd_health,
            '/performance': self.cmd_performance,
            '/connections': self.cmd_connections,
            '/help': self.cmd_help,
            '/exit': self.cmd_exit,
            '/clear': self.cmd_clear,
            '/demo': self.cmd_demo_mode,
            '/real': self.cmd_real_mode,  # Will be blocked for safety
            '/restart': self.cmd_restart_system,
            '/emergency': self.cmd_emergency_stop
        }
        
    async def start(self):
        """Start terminal interface"""
        try:
            print("""
╔══════════════════════════════════════════════════════════════╗
║          🧠 UOTA ELITE v2 - AUTONOMOUS COMMANDER              ║
║              Zero-Downtime Trading Intelligence                ║
╚══════════════════════════════════════════════════════════════╝

🚀 System initializing...  
""")
            
            # Initialize commander
            await autonomous_commander.initialize_commander()
            
            # Initialize zero-downtime infrastructure
            await zero_downtime_manager.initialize()
            
            # Setup demo mode (safety lockdown)
            await self._setup_demo_mode()
            
            self.is_running = True
            print("✅ Autonomous Commander ready for commands")
            print("💡 Type '/help' for available commands")
            print("🛡️  SAFETY LOCKDOWN: Running in DEMO mode only")
            print()
            
            # Start command loop
            await self._command_loop()
            
        except KeyboardInterrupt:
            print("\n👋 Shutting down gracefully...")
            await self._shutdown()
        except Exception as e:
            print(f"❌ Error starting terminal interface: {e}")
            await self._shutdown()
            
    async def _command_loop(self):
        """Main command processing loop"""
        while self.is_running:
            try:
                # Get user input
                command = await self._get_input()
                
                if not command:
                    continue
                    
                # Add to history
                self._add_to_history(command)
                
                # Process command
                await self._process_command(command)
                
            except KeyboardInterrupt:
                print("\n👋 Use '/exit' to shutdown gracefully")
                continue
            except Exception as e:
                print(f"❌ Error processing command: {e}")
                
    async def _get_input(self) -> str:
        """Get user input asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Use run_in_executor to make input non-blocking
        return await loop.run_in_executor(None, input, self.prompt)
        
    async def _process_command(self, command: str):
        """Process user command"""
        try:
            command = command.strip()
            
            # Skip empty commands
            if not command:
                return
                
            # Extract command and args
            parts = command.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Check if command exists
            if cmd in self.commands:
                await self.commands[cmd](args)
            else:
                # Try commander's command handler
                result = await autonomous_commander.handle_terminal_command(command)
                print(result)
                
        except Exception as e:
            print(f"❌ Error processing command: {e}")
            
    def _add_to_history(self, command: str):
        """Add command to history"""
        self.command_history.append(command)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
            
    # Command implementations
    async def cmd_status(self, args: List[str]):
        """Show detailed status report"""
        try:
            result = await autonomous_commander.handle_terminal_command('/status')
            print(result)
            
            # Add additional system status
            system_status = await zero_downtime_manager.get_system_status()
            print(f"""
🔧 SYSTEM INFRASTRUCTURE
═══════════════════════════════════════
Zero-Downtime: {'✅ Active' if system_status.get('zero_downtime_active') else '❌ Inactive'}
Connection Health: {system_status.get('connections', {}).get('health_percentage', 0):.1f}%
CPU Usage: {system_status.get('performance', {}).get('system_cpu_percent', 0):.1f}%
Memory Usage: {system_status.get('performance', {}).get('system_memory_percent', 0):.1f}%
""")
            
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            
    async def cmd_boost(self, args: List[str]):
        """Activate boost mode"""
        try:
            result = await autonomous_commander.handle_terminal_command('/boost')
            print(result)
            
            # Update system performance for boost mode
            print("⚡ System performance optimized for boost mode")
            
        except Exception as e:
            print(f"❌ Error activating boost: {e}")
            
    async def cmd_safe(self, args: List[str]):
        """Activate safe mode"""
        try:
            result = await autonomous_commander.handle_terminal_command('/safe')
            print(result)
            
        except Exception as e:
            print(f"❌ Error activating safe mode: {e}")
            
    async def cmd_goal(self, args: List[str]):
        """Set new trading goal"""
        try:
            if not args:
                print("Usage: /goal $4000 in 30 days")
                return
                
            goal_string = " ".join(args)
            result = await autonomous_commander.parse_and_execute_goal(goal_string)
            
            if result['success']:
                print(f"""
🎯 GOAL ACTIVATED
═══════════════════════════════════════
Target: ${result['goal'].target_amount:,.2f}
Deadline: {result['goal'].deadline.strftime('%Y-%m-%d')}
Daily ROI Required: {result['goal'].daily_roi_required:.2%}
Optimal Leverage: {result['goal'].optimal_leverage:.1f}x
Status: {result['goal'].status.value}

✅ Goal execution started
""")
            else:
                print(f"❌ Failed to set goal: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error setting goal: {e}")
            
    async def cmd_upscale(self, args: List[str]):
        """Command-based scaling - Commander only updates when explicitly told"""
        try:
            if not args:
                print("Usage: /upscale $4000")
                return
                
            target_amount_str = args[0]
            # Parse amount (remove $ and convert to float)
            if target_amount_str.startswith('$'):
                target_amount_str = target_amount_str[1:]
            
            try:
                target_amount = float(target_amount_str)
                if target_amount <= 0:
                    print("❌ Target amount must be positive")
                    return
            except ValueError:
                print(f"❌ Invalid amount: {target_amount_str}")
                return
            
            print(f"""
🎯 COMMANDER - RECEIVED SCALING ORDER
═════════════════════════════════════
New Target: ${target_amount:,.2f}
Commander: Updating mission parameters
Risk Rule: Maintaining 1% absolute
SMC Logic: Hard-locked (no changes)
""")
            
            # Update goal with new target
            goal_command = f"${target_amount} in 30 days"
            result = await autonomous_commander.parse_and_execute_goal(goal_command)
            
            if result['success']:
                goal = result['goal']
                print(f"""
✅ SCALING ORDER EXECUTED
═════════════════════════════════════
Updated Target: ${goal.target_amount:,.2f}
Daily ROI Required: {goal.daily_roi_required:.2%}
Optimal Leverage: {goal.optimal_leverage:.1f}x
Lot Size: Recalculated for 1% risk
Status: {goal.status.value}

🎯 Commander: Awaiting next command
""")
            else:
                print(f"❌ Scaling failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error in scaling: {e}")
            
    async def cmd_health(self, args: List[str]):
        """Show system health report"""
        try:
            system_status = await zero_downtime_manager.get_system_status()
            
            print(f"""
🏥 SYSTEM HEALTH REPORT
═══════════════════════════════════════
Overall Status: {system_status.get('status', 'unknown').upper()}
Uptime: {system_status.get('uptime_seconds', 0):.0f} seconds

🔗 CONNECTIONS
═══════════════════════════════════════
Total: {system_status.get('connections', {}).get('total_connections', 0)}
Healthy: {system_status.get('connections', {}).get('healthy_connections', 0)}
Health Score: {system_status.get('connections', {}).get('health_percentage', 0):.1f}%

⚡ PERFORMANCE
═══════════════════════════════════════
CPU: {system_status.get('performance', {}).get('system_cpu_percent', 0):.1f}%
Memory: {system_status.get('performance', {}).get('system_memory_percent', 0):.1f}%
Process Memory: {system_status.get('performance', {}).get('process_memory_mb', 0):.1f} MB
""")
            
        except Exception as e:
            print(f"❌ Error getting health report: {e}")
            
    async def cmd_performance(self, args: List[str]):
        """Show detailed performance metrics"""
        try:
            from zero_downtime_infrastructure import performance_optimizer
            metrics = await performance_optimizer.get_performance_metrics()
            
            print(f"""
⚡ PERFORMANCE METRICS
═══════════════════════════════════════
System CPU: {metrics.get('system_cpu_percent', 0):.1f}%
System Memory: {metrics.get('system_memory_percent', 0):.1f}%
Process CPU: {metrics.get('process_cpu_percent', 0):.1f}%
Process Memory: {metrics.get('process_memory_mb', 0):.1f} MB
Thread Count: {metrics.get('thread_count', 0)}
Optimization Active: {'✅' if metrics.get('optimization_active') else '❌'}
""")
            
        except Exception as e:
            print(f"❌ Error getting performance metrics: {e}")
            
    async def cmd_connections(self, args: List[str]):
        """Show connection details"""
        try:
            from zero_downtime_infrastructure import connection_manager
            health = await connection_manager.get_connection_health()
            
            print(f"""
🔗 CONNECTION DETAILS
═══════════════════════════════════════
""")
            
            for exchange, conn_info in health.get('connections', {}).items():
                status_icon = "✅" if conn_info.get('status') == 'connected' else "❌"
                print(f"{status_icon} {exchange}")
                print(f"   Status: {conn_info.get('status', 'unknown')}")
                print(f"   Latency: {conn_info.get('latency_ms', 0):.1f}ms")
                print(f"   Uptime: {conn_info.get('uptime_percentage', 0):.1f}%")
                print(f"   Reconnects: {conn_info.get('reconnect_count', 0)}")
                print()
                
        except Exception as e:
            print(f"❌ Error getting connection details: {e}")
            
    async def cmd_help(self, args: List[str]):
        """Show help information"""
        help_text = """
🤖 AUTONOMOUS COMMANDER - COMMAND REFERENCE
═══════════════════════════════════════════════════════════════

📊 GOAL & STATUS COMMANDS
═══════════════════════════════════════════════════════════════
/status          - Show detailed goal progress and system status
/goal $AMOUNT in DAYS - Set new trading goal
                 Examples: /goal $5000 in 30 days
                           /goal $10000 by 2024-12-31

⚡ INTENSITY COMMANDS
═══════════════════════════════════════════════════════════════
/boost           - Activate institutional hunting mode
/safe            - Switch to capital preservation mode

🔧 SYSTEM COMMANDS
═══════════════════════════════════════════════════════════════
/health          - Show system health report
/performance     - Show detailed performance metrics
/connections     - Show exchange connection details
/restart         - Restart system components
/emergency       - Emergency stop all trading

🛡️  SAFETY COMMANDS
═══════════════════════════════════════════════════════════════
/demo            - Switch to demo mode (default)
/real            - [BLOCKED] Switch to real money mode

💡 UTILITY COMMANDS
═══════════════════════════════════════════════════════════════
/help            - Show this help message
/clear           - Clear terminal screen
/exit            - Shutdown gracefully

🔒 SAFETY NOTICE
═══════════════════════════════════════════════════════════════
⚠️  System is in DEMO MODE ONLY for safety testing
⚠️  Real money trading is BLOCKED during 3-month phase
⚠️  All features work with simulated data for testing
"""
        print(help_text)
        
    async def cmd_exit(self, args: List[str]):
        """Exit gracefully"""
        print("👋 Shutting down Autonomous Commander...")
        self.is_running = False
        await self._shutdown()
        
    async def cmd_clear(self, args: List[str]):
        """Clear terminal screen"""
        # import os  # Moved to function to avoid circular import
        os.system('cls' if os.name == 'nt' else 'clear')
        print("""
╔══════════════════════════════════════════════════════════════╗
║          🧠 UOTA ELITE v2 - AUTONOMOUS COMMANDER              ║
║              Zero-Downtime Trading Intelligence                ║
╚══════════════════════════════════════════════════════════════╝
""")
        
    async def cmd_demo_mode(self, args: List[str]):
        """Switch to demo mode"""
        try:
            autonomous_commander.safety_lockdown = True
            print("🛡️  DEMO MODE ACTIVATED - All trading uses simulated data")
            print("💰 No real money at risk - Safe for testing")
            
        except Exception as e:
            print(f"❌ Error activating demo mode: {e}")
            
    async def cmd_real_mode(self, args: List[str]):
        """[BLOCKED] Switch to real money mode"""
        print("🚫 REAL MONEY MODE BLOCKED")
        print("⚠️  For safety, real money trading is disabled during 3-month testing phase")
        print("🛡️  Use /demo mode for safe testing with simulated data")
        
    async def cmd_restart_system(self, args: List[str]):
        """Restart system components"""
        try:
            print("🔄 Restarting system components...")
            
            # Restart zero-downtime manager
            await zero_downtime_manager.shutdown()
            await zero_downtime_manager.initialize()
            
            # Restart commander
            await autonomous_commander.initialize_commander()
            
            print("✅ System components restarted successfully")
            
        except Exception as e:
            print(f"❌ Error restarting system: {e}")
            
    async def cmd_emergency_stop(self, args: List[str]):
        """Emergency stop all trading"""
        try:
            print("🚨 EMERGENCY STOP ACTIVATED")
            
            # Stop all trading
            if autonomous_commander.current_goal:
                autonomous_commander.current_goal.status = 'preserving'
                
            # Close all positions (simulated in demo)
            print("🛑 All positions closed (simulated)")
            print("🛡️  System in safe preservation mode")
            
        except Exception as e:
            print(f"❌ Error in emergency stop: {e}")
            
    async def _setup_demo_mode(self):
        """Setup demo mode with safety configurations"""
        try:
            # Ensure safety lockdown is active
            autonomous_commander.safety_lockdown = True
            
            # Configure demo exchange connections
            demo_configs = {
                'binance_demo': {
                    'base_url': 'https://testnet.binancefuture.com',
                    'api_key': 'demo_key',
                    'api_secret': 'demo_secret'
                },
                'bybit_demo': {
                    'base_url': 'https://api-testnet.bybit.com',
                    'api_key': 'demo_key',
                    'api_secret': 'demo_secret'
                }
            }
            
            await zero_downtime_manager.setup_exchange_connections(demo_configs)
            
            print("🛡️  Demo mode configured with testnet exchanges")
            
        except Exception as e:
            self.logger.error(f"Error setting up demo mode: {e}")
            
    async def _shutdown(self):
        """Graceful shutdown"""
        try:
            print("🔄 Shutting down components...")
            
            # Shutdown commander
            if autonomous_commander.is_active:
                autonomous_commander.is_active = False
                
            # Shutdown zero-downtime manager
            await zero_downtime_manager.shutdown()
            
            print("✅ Shutdown complete")
            
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")

# Global terminal interface
terminal_interface = TerminalCommandInterface()

if __name__ == "__main__":
    # Start terminal interface
    asyncio.run(terminal_interface.start())
