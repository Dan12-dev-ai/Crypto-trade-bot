#!/usr/bin/env python3
"""
UOTA Elite v2 - Institutional Security System
IP locking decorators and environment validation for institutional-grade security
"""

import asyncio
import logging
import sys
import os
import socket
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import requests
import ipaddress

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security clearance levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CRITICAL = "critical"

class ValidationStatus(Enum):
    """IP validation status"""
    APPROVED = "approved"
    DENIED = "denied"
    PENDING = "pending"
    EXPIRED = "expired"

@dataclass
class IPWhitelistEntry:
    """IP whitelist entry"""
    ip_address: str
    description: str
    security_level: SecurityLevel
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    request_count: int = 0
    last_used: Optional[datetime] = None

@dataclass
class SecurityEvent:
    """Security event log"""
    event_id: str
    event_type: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    status: ValidationStatus
    details: Dict[str, Any]
    risk_score: float = 0.0

class IPValidator:
    """Institutional-grade IP validation and security system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        
        # Security configuration
        self.allowed_vps_ips = [
            # Production VPS IPs would be added here
            # Example: "192.168.1.100", "10.0.0.50"
        ]
        
        self.exchange_ips = {
            'binance': ['0.0.0.0/0'],  # Would contain actual Binance IPs
            'bybit': ['0.0.0.0/0'],     # Would contain actual Bybit IPs
            'okx': ['0.0.0.0/0'],        # Would contain actual OKX IPs
            'hyperliquid': ['0.0.0.0/0']  # Would contain actual Hyperliquid IPs
        }
        
        # Rate limiting
        self.rate_limits = {
            'execution': 10,      # 10 requests per minute
            'api_call': 100,      # 100 requests per minute
            'auth': 5,           # 5 auth attempts per minute
            'emergency': 1        # 1 emergency action per minute
        }
        
        # Security state
        self.ip_whitelist = []
        self.security_events = []
        self.blocked_ips = {}
        self.rate_limit_tracker = {}
        
        # Security thresholds
        self.max_failed_attempts = 5
        self.block_duration = timedelta(hours=1)
        self.high_risk_threshold = 0.8
        
    async def initialize(self) -> None:
        """Initialize IP validator"""
        try:
            self.logger.info("🔒 Initializing IP Validator")
            
            # Create security directory
            Path('data/security').mkdir(exist_ok=True)
            
            # Load IP whitelist
            await self._load_ip_whitelist()
            
            # Load security events
            await self._load_security_events()
            
            # Load blocked IPs
            await self._load_blocked_ips()
            
            # Get current IP
            current_ip = await self._get_current_ip()
            if current_ip:
                self.logger.info(f"🌐 Current IP: {current_ip}")
                
                # Auto-add current IP to whitelist if not present
                if not await self._is_ip_whitelisted(current_ip):
                    await self._add_ip_to_whitelist(
                        current_ip, 
                        "Auto-added current IP",
                        SecurityLevel.INTERNAL
                    )
            
            self.is_initialized = True
            self.logger.info("✅ IP Validator initialized")
            
        except Exception as e:
            self.logger.error(f"❌ IP Validator initialization failed: {e}")
            raise
    
    def validate_ip(self, security_level: SecurityLevel = SecurityLevel.INTERNAL):
        """Decorator to validate IP for function execution"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Check if validator is initialized
                if not self.is_initialized:
                    self.logger.error("❌ IP Validator not initialized")
                    raise SecurityError("IP Validator not initialized")
                
                # Get client IP
                client_ip = await self._get_client_ip()
                if not client_ip:
                    self.logger.error("❌ Could not determine client IP")
                    raise SecurityError("Could not determine client IP")
                
                # Validate IP
                validation_result = await self._validate_ip_address(
                    client_ip, security_level
                )
                
                # Log security event
                await self._log_security_event(
                    event_type="function_access",
                    ip_address=client_ip,
                    status=validation_result['status'],
                    details={
                        'function': func.__name__,
                        'security_level': security_level.value,
                        'validation_reason': validation_result['reason']
                    }
                )
                
                # Check if approved
                if validation_result['status'] != ValidationStatus.APPROVED:
                    self.logger.warning(f"🚫 Access denied for {client_ip}: {validation_result['reason']}")
                    raise SecurityError(f"Access denied: {validation_result['reason']}")
                
                # Execute function
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    # Log function execution error
                    await self._log_security_event(
                        event_type="function_error",
                        ip_address=client_ip,
                        status=ValidationStatus.DENIED,
                        details={
                            'function': func.__name__,
                            'error': str(e)
                        }
                    )
                    raise
            
            return wrapper
        return decorator
    
    def validate_execution_environment(self):
        """Validate execution environment for trading operations"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Check if validator is initialized
                if not self.is_initialized:
                    raise SecurityError("IP Validator not initialized")
                
                # Get client IP
                client_ip = await self._get_client_ip()
                if not client_ip:
                    raise SecurityError("Could not determine client IP")
                
                # Validate for execution (highest security)
                validation_result = await self._validate_execution_environment(client_ip)
                
                # Log security event
                await self._log_security_event(
                    event_type="execution_attempt",
                    ip_address=client_ip,
                    status=validation_result['status'],
                    details={
                        'function': func.__name__,
                        'validation_result': validation_result
                    }
                )
                
                # Check if approved
                if not validation_result['approved']:
                    self.logger.warning(f"🚫 Execution denied for {client_ip}: {validation_result['reason']}")
                    raise SecurityError(f"Execution denied: {validation_result['reason']}")
                
                # Execute function
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    await self._log_security_event(
                        event_type="execution_error",
                        ip_address=client_ip,
                        status=ValidationStatus.DENIED,
                        details={
                            'function': func.__name__,
                            'error': str(e)
                        }
                    )
                    raise
            
            return wrapper
        return decorator
    
    async def _validate_ip_address(self, ip_address: str, 
                                 security_level: SecurityLevel) -> Dict[str, Any]:
        """Validate IP address against whitelist"""
        try:
            # Check if IP is blocked
            if ip_address in self.blocked_ips:
                block_info = self.blocked_ips[ip_address]
                if datetime.now() < block_info['expires_at']:
                    return {
                        'status': ValidationStatus.DENIED,
                        'reason': f"IP blocked until {block_info['expires_at']}",
                        'risk_score': 1.0
                    }
                else:
                    # Block expired, remove it
                    del self.blocked_ips[ip_address]
            
            # Check whitelist
            for entry in self.ip_whitelist:
                if not entry.is_active:
                    continue
                
                # Check expiration
                if entry.expires_at and datetime.now() > entry.expires_at:
                    entry.is_active = False
                    continue
                
                # Check IP match
                if self._ip_matches(ip_address, entry.ip_address):
                    # Check security level
                    if self._security_level_allowed(entry.security_level, security_level):
                        # Update usage
                        entry.request_count += 1
                        entry.last_used = datetime.now()
                        
                        return {
                            'status': ValidationStatus.APPROVED,
                            'reason': f"IP whitelisted with level {entry.security_level.value}",
                            'risk_score': 0.1,
                            'entry': entry
                        }
                    else:
                        return {
                            'status': ValidationStatus.DENIED,
                            'reason': f"Insufficient security level. Required: {security_level.value}, Has: {entry.security_level.value}",
                            'risk_score': 0.7
                        }
            
            # IP not in whitelist
            return {
                'status': ValidationStatus.DENIED,
                'reason': "IP not in whitelist",
                'risk_score': 0.9
            }
            
        except Exception as e:
            self.logger.error(f"❌ IP validation failed: {e}")
            return {
                'status': ValidationStatus.DENIED,
                'reason': f"Validation error: {str(e)}",
                'risk_score': 1.0
            }
    
    async def _validate_execution_environment(self, ip_address: str) -> Dict[str, Any]:
        """Validate environment for trading execution"""
        try:
            # Basic IP validation
            ip_validation = await self._validate_ip_address(ip_address, SecurityLevel.CRITICAL)
            if ip_validation['status'] != ValidationStatus.APPROVED:
                return {
                    'approved': False,
                    'reason': ip_validation['reason'],
                    'risk_score': ip_validation['risk_score']
                }
            
            # Check rate limiting
            rate_limit_check = await self._check_rate_limit('execution', ip_address)
            if not rate_limit_check['allowed']:
                return {
                    'approved': False,
                    'reason': f"Rate limit exceeded: {rate_limit_check['reason']}",
                    'risk_score': 0.8
                }
            
            # Check environment variables
            env_check = await self._check_environment_security()
            if not env_check['secure']:
                return {
                    'approved': False,
                    'reason': f"Environment security issue: {env_check['issue']}",
                    'risk_score': 0.9
                }
            
            # Check system integrity
            integrity_check = await self._check_system_integrity()
            if not integrity_check['integrity_ok']:
                return {
                    'approved': False,
                    'reason': f"System integrity issue: {integrity_check['issue']}",
                    'risk_score': 1.0
                }
            
            return {
                'approved': True,
                'reason': "Execution environment validated",
                'risk_score': 0.1
            }
            
        except Exception as e:
            self.logger.error(f"❌ Execution environment validation failed: {e}")
            return {
                'approved': False,
                'reason': f"Validation error: {str(e)}",
                'risk_score': 1.0
            }
    
    async def _get_client_ip(self) -> Optional[str]:
        """Get client IP address"""
        try:
            # Try to get external IP
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            if response.status_code == 200:
                return response.json()['ip']
            
            # Fallback to local IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get client IP: {e}")
            return None
    
    async def _get_current_ip(self) -> Optional[str]:
        """Get current server IP"""
        try:
            # Get external IP
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            if response.status_code == 200:
                return response.json()['ip']
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get current IP: {e}")
            return None
    
    def _ip_matches(self, ip_address: str, whitelist_entry: str) -> bool:
        """Check if IP matches whitelist entry"""
        try:
            # Handle CIDR notation
            if '/' in whitelist_entry:
                network = ipaddress.ip_network(whitelist_entry, strict=False)
                return ipaddress.ip_address(ip_address) in network
            
            # Exact match
            return ip_address == whitelist_entry
            
        except Exception as e:
            self.logger.error(f"❌ IP matching failed: {e}")
            return False
    
    def _security_level_allowed(self, entry_level: SecurityLevel, 
                              required_level: SecurityLevel) -> bool:
        """Check if security level is allowed"""
        level_hierarchy = {
            SecurityLevel.PUBLIC: 0,
            SecurityLevel.INTERNAL: 1,
            SecurityLevel.RESTRICTED: 2,
            SecurityLevel.CRITICAL: 3
        }
        
        return level_hierarchy[entry_level] >= level_hierarchy[required_level]
    
    async def _check_rate_limit(self, action_type: str, ip_address: str) -> Dict[str, Any]:
        """Check rate limiting"""
        try:
            current_time = time.time()
            key = f"{action_type}:{ip_address}"
            
            # Clean old entries
            if key in self.rate_limit_tracker:
                self.rate_limit_tracker[key] = [
                    timestamp for timestamp in self.rate_limit_tracker[key]
                    if current_time - timestamp < 60  # Keep last minute
                ]
            else:
                self.rate_limit_tracker[key] = []
            
            # Check limit
            request_count = len(self.rate_limit_tracker[key])
            limit = self.rate_limits.get(action_type, 10)
            
            if request_count >= limit:
                return {
                    'allowed': False,
                    'reason': f"Rate limit exceeded: {request_count}/{limit} per minute",
                    'current_count': request_count,
                    'limit': limit
                }
            
            # Add current request
            self.rate_limit_tracker[key].append(current_time)
            
            return {
                'allowed': True,
                'reason': "Rate limit OK",
                'current_count': request_count + 1,
                'limit': limit
            }
            
        except Exception as e:
            self.logger.error(f"❌ Rate limit check failed: {e}")
            return {
                'allowed': False,
                'reason': f"Rate limit check error: {str(e)}"
            }
    
    async def _check_environment_security(self) -> Dict[str, Any]:
        """Check environment security"""
        try:
            # Check for required environment variables
            required_vars = ['EXCHANGE_API_KEY', 'TELEGRAM_BOT_TOKEN']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                return {
                    'secure': False,
                    'issue': f"Missing environment variables: {missing_vars}"
                }
            
            # Check for debug mode
            if os.getenv('DEBUG', 'false').lower() == 'true':
                return {
                    'secure': False,
                    'issue': "Debug mode enabled"
                }
            
            # Check file permissions
            sensitive_files = ['.env', 'config/credentials.json']
            for file_path in sensitive_files:
                if Path(file_path).exists():
                    stat = Path(file_path).stat()
                    if stat.st_mode & 0o077:  # Check if others have read/write access
                        return {
                            'secure': False,
                            'issue': f"Insecure file permissions: {file_path}"
                        }
            
            return {
                'secure': True,
                'issue': None
            }
            
        except Exception as e:
            self.logger.error(f"❌ Environment security check failed: {e}")
            return {
                'secure': False,
                'issue': f"Security check error: {str(e)}"
            }
    
    async def _check_system_integrity(self) -> Dict[str, Any]:
        """Check system integrity"""
        try:
            # Check for suspicious processes
            suspicious_processes = ['wireshark', 'tcpdump', 'strace']
            
            # Check for modified files
            critical_files = ['main_orchestrator.py', 'execution/consensus_engine.py']
            
            # Simple integrity check (would be more sophisticated in production)
            for file_path in critical_files:
                if Path(file_path).exists():
                    # Check file modification time
                    stat = Path(file_path).stat()
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # If file was modified very recently, it might be suspicious
                    if datetime.now() - mod_time < timedelta(minutes=5):
                        return {
                            'integrity_ok': False,
                            'issue': f"Recent modification detected: {file_path}"
                        }
            
            return {
                'integrity_ok': True,
                'issue': None
            }
            
        except Exception as e:
            self.logger.error(f"❌ System integrity check failed: {e}")
            return {
                'integrity_ok': False,
                'issue': f"Integrity check error: {str(e)}"
            }
    
    async def _add_ip_to_whitelist(self, ip_address: str, description: str,
                                 security_level: SecurityLevel,
                                 expires_at: Optional[datetime] = None) -> None:
        """Add IP to whitelist"""
        try:
            entry = IPWhitelistEntry(
                ip_address=ip_address,
                description=description,
                security_level=security_level,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            self.ip_whitelist.append(entry)
            await self._save_ip_whitelist()
            
            self.logger.info(f"✅ Added IP {ip_address} to whitelist: {description}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add IP to whitelist: {e}")
    
    async def _is_ip_whitelisted(self, ip_address: str) -> bool:
        """Check if IP is whitelisted"""
        try:
            for entry in self.ip_whitelist:
                if not entry.is_active:
                    continue
                
                if entry.expires_at and datetime.now() > entry.expires_at:
                    entry.is_active = False
                    continue
                
                if self._ip_matches(ip_address, entry.ip_address):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Whitelist check failed: {e}")
            return False
    
    async def _log_security_event(self, event_type: str, ip_address: str,
                               status: ValidationStatus,
                               details: Dict[str, Any]) -> None:
        """Log security event"""
        try:
            event = SecurityEvent(
                event_id=f"sec_{datetime.now().timestamp()}",
                event_type=event_type,
                ip_address=ip_address,
                user_agent="UOTA_Elite_v2",
                timestamp=datetime.now(),
                status=status,
                details=details,
                risk_score=details.get('risk_score', 0.5)
            )
            
            self.security_events.append(event)
            
            # Keep only last 1000 events
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]
            
            # Save to file
            events_file = Path('data/security/security_events.json')
            with open(events_file, 'w') as f:
                json.dump([self._event_to_dict(e) for e in self.security_events], f, indent=2, default=str)
            
            # Check for high-risk events
            if event.risk_score > self.high_risk_threshold:
                await self._handle_high_risk_event(event)
            
        except Exception as e:
            self.logger.error(f"❌ Security event logging failed: {e}")
    
    async def _handle_high_risk_event(self, event: SecurityEvent) -> None:
        """Handle high-risk security events"""
        try:
            self.logger.warning(f"🚨 High-risk security event: {event.event_type} from {event.ip_address}")
            
            # Block IP if necessary
            if event.event_type in ['execution_attempt', 'function_access'] and event.status == ValidationStatus.DENIED:
                await self._block_ip_temporarily(event.ip_address)
            
            # Send alert (would integrate with Telegram)
            # await self._send_security_alert(event)
            
        except Exception as e:
            self.logger.error(f"❌ High-risk event handling failed: {e}")
    
    async def _block_ip_temporarily(self, ip_address: str) -> None:
        """Block IP temporarily"""
        try:
            self.blocked_ips[ip_address] = {
                'blocked_at': datetime.now(),
                'expires_at': datetime.now() + self.block_duration,
                'reason': 'Multiple failed attempts'
            }
            
            await self._save_blocked_ips()
            self.logger.warning(f"🚫 Blocked IP {ip_address} until {self.blocked_ips[ip_address]['expires_at']}")
            
        except Exception as e:
            self.logger.error(f"❌ IP blocking failed: {e}")
    
    def _event_to_dict(self, event: SecurityEvent) -> Dict[str, Any]:
        """Convert security event to dictionary"""
        return {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'ip_address': event.ip_address,
            'timestamp': event.timestamp.isoformat(),
            'status': event.status.value,
            'details': event.details,
            'risk_score': event.risk_score
        }
    
    async def _load_ip_whitelist(self) -> None:
        """Load IP whitelist from file"""
        try:
            whitelist_file = Path('data/security/ip_whitelist.json')
            if whitelist_file.exists():
                with open(whitelist_file, 'r') as f:
                    data = json.load(f)
                    
                    for entry_data in data:
                        entry = IPWhitelistEntry(
                            ip_address=entry_data['ip_address'],
                            description=entry_data['description'],
                            security_level=SecurityLevel(entry_data['security_level']),
                            created_at=datetime.fromisoformat(entry_data['created_at']),
                            expires_at=datetime.fromisoformat(entry_data['expires_at']) if entry_data.get('expires_at') else None,
                            is_active=entry_data.get('is_active', True),
                            request_count=entry_data.get('request_count', 0),
                            last_used=datetime.fromisoformat(entry_data['last_used']) if entry_data.get('last_used') else None
                        )
                        self.ip_whitelist.append(entry)
            
            self.logger.info(f"📚 Loaded {len(self.ip_whitelist)} whitelist entries")
            
        except Exception as e:
            self.logger.error(f"❌ Loading whitelist failed: {e}")
    
    async def _save_ip_whitelist(self) -> None:
        """Save IP whitelist to file"""
        try:
            whitelist_file = Path('data/security/ip_whitelist.json')
            data = []
            
            for entry in self.ip_whitelist:
                data.append({
                    'ip_address': entry.ip_address,
                    'description': entry.description,
                    'security_level': entry.security_level.value,
                    'created_at': entry.created_at.isoformat(),
                    'expires_at': entry.expires_at.isoformat() if entry.expires_at else None,
                    'is_active': entry.is_active,
                    'request_count': entry.request_count,
                    'last_used': entry.last_used.isoformat() if entry.last_used else None
                })
            
            with open(whitelist_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"❌ Saving whitelist failed: {e}")
    
    async def _load_security_events(self) -> None:
        """Load security events from file"""
        try:
            events_file = Path('data/security/security_events.json')
            if events_file.exists():
                with open(events_file, 'r') as f:
                    data = json.load(f)
                    
                    for event_data in data:
                        event = SecurityEvent(
                            event_id=event_data['event_id'],
                            event_type=event_data['event_type'],
                            ip_address=event_data['ip_address'],
                            user_agent=event_data.get('user_agent', ''),
                            timestamp=datetime.fromisoformat(event_data['timestamp']),
                            status=ValidationStatus(event_data['status']),
                            details=event_data['details'],
                            risk_score=event_data.get('risk_score', 0.5)
                        )
                        self.security_events.append(event)
            
            self.logger.info(f"📚 Loaded {len(self.security_events)} security events")
            
        except Exception as e:
            self.logger.error(f"❌ Loading security events failed: {e}")
    
    async def _load_blocked_ips(self) -> None:
        """Load blocked IPs from file"""
        try:
            blocked_file = Path('data/security/blocked_ips.json')
            if blocked_file.exists():
                with open(blocked_file, 'r') as f:
                    data = json.load(f)
                    self.blocked_ips = data
                
                # Clean expired blocks
                current_time = datetime.now()
                expired_ips = [
                    ip for ip, block_info in self.blocked_ips.items()
                    if current_time > datetime.fromisoformat(block_info['expires_at'])
                ]
                
                for ip in expired_ips:
                    del self.blocked_ips[ip]
                
                if expired_ips:
                    await self._save_blocked_ips()
            
            self.logger.info(f"🚫 Loaded {len(self.blocked_ips)} blocked IPs")
            
        except Exception as e:
            self.logger.error(f"❌ Loading blocked IPs failed: {e}")
    
    async def _save_blocked_ips(self) -> None:
        """Save blocked IPs to file"""
        try:
            blocked_file = Path('data/security/blocked_ips.json')
            with open(blocked_file, 'w') as f:
                json.dump(self.blocked_ips, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"❌ Saving blocked IPs failed: {e}")

# Global IP validator instance
ip_validator = IPValidator()

# Decorator functions for easy use
def validate_ip(security_level: SecurityLevel = SecurityLevel.INTERNAL):
    """Validate IP decorator"""
    return ip_validator.validate_ip(security_level)

def validate_execution_environment():
    """Validate execution environment decorator"""
    return ip_validator.validate_execution_environment()

class SecurityError(Exception):
    """Security-related exceptions"""
    pass

# Main execution for testing
async def main():
    """Test IP validator"""
    validator = IPValidator()
    
    try:
        await validator.initialize()
        
        # Test IP validation
        current_ip = await validator._get_current_ip()
        if current_ip:
            result = await validator._validate_ip_address(current_ip, SecurityLevel.INTERNAL)
            print(f"IP validation result: {result['status'].value}")
            print(f"Reason: {result['reason']}")
        
        # Test environment security
        env_check = await validator._check_environment_security()
        print(f"Environment security: {env_check}")
        
        # Test system integrity
        integrity_check = await validator._check_system_integrity()
        print(f"System integrity: {integrity_check}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
