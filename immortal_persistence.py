#!/usr/bin/env python3
"""
UOTA Elite v2 - Immortal Persistence
The Watchdog: Heartbeat system and state persistence
"""

import os
import json
import time
import logging
import threading
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

class ImmortalPersistence:
    """Immoral persistence system with heartbeat and state management"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.heartbeat_file = 'logs/heartbeat.log'
        self.session_file = 'data/session.json'
        self.state_file = 'data/bot_state.json'
        
        # Heartbeat configuration
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 120  # 2 minutes
        self.last_heartbeat = None
        
        # State persistence
        self.current_state = {
            'mission': None,
            'active_trades': [],
            'session_start': None,
            'last_restart': None,
            'restart_count': 0
        }
        
        # Watchdog process
        self.watchdog_process = None
        self.is_running = False
        
    def _setup_logging(self):
        """Setup logging for immortal persistence"""
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/immortal_persistence.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def write_heartbeat(self):
        """Write heartbeat to file"""
        try:
            heartbeat_data = {
                'timestamp': datetime.now().isoformat(),
                'status': 'ALIVE',
                'pid': os.getpid(),
                'memory_usage': psutil.Process().memory_info().rss / 1024 / 1024,  # MB
                'cpu_usage': psutil.cpu_percent(interval=1),
                'active_trades': len(self.current_state['active_trades']),
                'mission_active': self.current_state['mission'] is not None
            }
            
            with open(self.heartbeat_file, 'w') as f:
                json.dump(heartbeat_data, f, indent=2)
            
            self.last_heartbeat = datetime.now()
            self.logger.debug("💓 Heartbeat written")
            
        except Exception as e:
            self.logger.error(f"❌ Error writing heartbeat: {e}")
    
    def check_heartbeat(self) -> bool:
        """Check if heartbeat is recent"""
        try:
            if not os.path.exists(self.heartbeat_file):
                self.logger.warning("⚠️ Heartbeat file not found")
                return False
            
            with open(self.heartbeat_file, 'r') as f:
                heartbeat_data = json.load(f)
            
            last_heartbeat_time = datetime.fromisoformat(heartbeat_data['timestamp'])
            time_since_heartbeat = datetime.now() - last_heartbeat_time
            
            is_alive = time_since_heartbeat.total_seconds() < self.heartbeat_timeout
            
            if not is_alive:
                self.logger.warning(f"⚠️ Heartbeat timeout: {time_since_heartbeat.total_seconds():.1f}s ago")
            
            return is_alive
            
        except Exception as e:
            self.logger.error(f"❌ Error checking heartbeat: {e}")
            return False
    
    def save_state(self):
        """Save current state to file"""
        try:
            state_data = {
                'timestamp': datetime.now().isoformat(),
                'mission': self.current_state['mission'],
                'active_trades': self.current_state['active_trades'],
                'session_start': self.current_state['session_start'],
                'last_restart': self.current_state['last_restart'],
                'restart_count': self.current_state['restart_count'],
                'bot_pid': os.getpid(),
                'memory_usage': psutil.Process().memory_info().rss / 1024 / 1024,
                'cpu_usage': psutil.cpu_percent(interval=1)
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            self.logger.debug("💾 State saved")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving state: {e}")
    
    def load_state(self):
        """Load state from file"""
        try:
            if not os.path.exists(self.state_file):
                self.logger.info("📄 State file not found, starting fresh")
                return False
            
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            
            # Restore state
            self.current_state['mission'] = state_data.get('mission')
            self.current_state['active_trades'] = state_data.get('active_trades', [])
            self.current_state['session_start'] = state_data.get('session_start')
            self.current_state['last_restart'] = state_data.get('last_restart')
            self.current_state['restart_count'] = state_data.get('restart_count', 0)
            
            self.logger.info(f"📂 State loaded: {len(self.current_state['active_trades'])} active trades")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error loading state: {e}")
            return False
    
    def update_mission(self, mission_data: Dict):
        """Update mission state"""
        try:
            self.current_state['mission'] = mission_data
            self.save_state()
            self.logger.info(f"🎯 Mission updated: {mission_data.get('target', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"❌ Error updating mission: {e}")
    
    def add_active_trade(self, trade_data: Dict):
        """Add active trade to state"""
        try:
            # Check if trade already exists
            existing_trade = next((t for t in self.current_state['active_trades'] 
                                if t.get('ticket') == trade_data.get('ticket')), None)
            
            if existing_trade:
                # Update existing trade
                existing_trade.update(trade_data)
                self.logger.debug(f"🔄 Updated existing trade: {trade_data.get('ticket')}")
            else:
                # Add new trade
                self.current_state['active_trades'].append(trade_data)
                self.logger.info(f"📈 Added active trade: {trade_data.get('ticket')}")
            
            self.save_state()
            
        except Exception as e:
            self.logger.error(f"❌ Error adding active trade: {e}")
    
    def remove_active_trade(self, ticket: int):
        """Remove active trade from state"""
        try:
            original_count = len(self.current_state['active_trades'])
            self.current_state['active_trades'] = [
                t for t in self.current_state['active_trades'] 
                if t.get('ticket') != ticket
            ]
            
            if len(self.current_state['active_trades']) < original_count:
                self.logger.info(f"📉 Removed active trade: {ticket}")
                self.save_state()
            else:
                self.logger.warning(f"⚠️ Trade {ticket} not found in active trades")
            
        except Exception as e:
            self.logger.error(f"❌ Error removing active trade: {e}")
    
    def get_active_trades(self) -> List[Dict]:
        """Get list of active trades"""
        return self.current_state['active_trades'].copy()
    
    def get_mission_state(self) -> Dict:
        """Get current mission state"""
        return self.current_state['mission'].copy() if self.current_state['mission'] else None
    
    def start_session(self):
        """Start new session"""
        try:
            self.current_state['session_start'] = datetime.now().isoformat()
            self.current_state['last_restart'] = datetime.now().isoformat()
            self.current_state['restart_count'] += 1
            
            self.save_state()
            self.logger.info(f"🚀 Session started: Restart #{self.current_state['restart_count']}")
            
        except Exception as e:
            self.logger.error(f"❌ Error starting session: {e}")
    
    def start_heartbeat_monitoring(self):
        """Start heartbeat monitoring in separate thread"""
        def heartbeat_loop():
            while self.is_running:
                try:
                    self.write_heartbeat()
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    self.logger.error(f"❌ Error in heartbeat loop: {e}")
                    time.sleep(self.heartbeat_interval)
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        self.logger.info("💓 Heartbeat monitoring started")
    
    def start_watchdog_process(self):
        """Start separate watchdog process"""
        try:
            import subprocess
            
            # Start watchdog process
            self.watchdog_process = subprocess.Popen([
                'python', 'watchdog_monitor.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.logger.info(f"🐕 Watchdog process started: PID {self.watchdog_process.pid}")
            
        except Exception as e:
            self.logger.error(f"❌ Error starting watchdog process: {e}")
    
    def force_restart_bot(self):
        """Force restart the bot"""
        try:
            self.logger.warning("🔄 Force restarting bot...")
            
            # Save current state before restart
            self.save_state()
            
            # Start new bot process
            import subprocess
            
            new_process = subprocess.Popen([
                'python', 'minimal_master_controller.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.logger.info(f"🚀 Bot restarted: PID {new_process.pid}")
            
            # Stop current process
            self.is_running = False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error force restarting bot: {e}")
            return False
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'heartbeat_active': self.last_heartbeat is not None,
                'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                'session_active': self.current_state['session_start'] is not None,
                'mission_active': self.current_state['mission'] is not None,
                'active_trades_count': len(self.current_state['active_trades']),
                'restart_count': self.current_state['restart_count'],
                'session_duration': None,
                'system_resources': {
                    'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                    'cpu_usage_percent': psutil.cpu_percent(interval=1),
                    'disk_usage_percent': psutil.disk_usage('/').percent
                }
            }
            
            # Calculate session duration
            if self.current_state['session_start']:
                start_time = datetime.fromisoformat(self.current_state['session_start'])
                status['session_duration'] = str(datetime.now() - start_time)
            
            return status
            
        except Exception as e:
            self.logger.error(f"❌ Error getting system status: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self):
        """Clean up old data files"""
        try:
            # Clean up old heartbeat files
            if os.path.exists(self.heartbeat_file):
                # Keep only last 100 heartbeat entries
                pass
            
            # Clean up old session files
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # Archive old state files
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                
                if state_data.get('session_start'):
                    session_time = datetime.fromisoformat(state_data['session_start'])
                    if session_time < cutoff_date:
                        # Archive old session
                        archive_file = f"data/session_archive_{session_time.strftime('%Y%m%d_%H%M%S')}.json"
                        with open(archive_file, 'w') as f:
                            json.dump(state_data, f, indent=2)
                        
                        self.logger.info(f"📦 Archived old session: {archive_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old data: {e}")
    
    def run_immortal_persistence(self):
        """Run immortal persistence system"""
        try:
            self.logger.info("🔄 Starting Immortal Persistence...")
            
            # Load existing state
            self.load_state()
            
            # Start session
            if not self.current_state['session_start']:
                self.start_session()
            
            # Start heartbeat monitoring
            self.start_heartbeat_monitoring()
            
            # Start watchdog process
            self.start_watchdog_process()
            
            # Set running state
            self.is_running = True
            
            self.logger.info("✅ Immortal Persistence started")
            
            # Keep running
            while self.is_running:
                try:
                    # Check heartbeat health
                    if not self.check_heartbeat():
                        self.logger.warning("🚨 Heartbeat failure detected - Force restarting")
                        self.force_restart_bot()
                        break
                    
                    # Cleanup old data periodically
                    if datetime.now().minute % 30 == 0:  # Every 30 minutes
                        self.cleanup_old_data()
                    
                    time.sleep(60)  # Check every minute
                    
                except KeyboardInterrupt:
                    self.logger.info("🛑 Immortal Persistence stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"❌ Error in main loop: {e}")
                    time.sleep(60)
            
            # Cleanup
            self.save_state()
            self.logger.info("🧹 Immortal Persistence cleanup complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error in immortal persistence: {e}")

# Global immortal persistence instance
immortal_persistence = ImmortalPersistence()
