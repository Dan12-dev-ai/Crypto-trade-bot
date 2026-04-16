#!/usr/bin/env python3
"""
UOTA Elite v2 - Security Manager
Encryption, firewall, and anti-hacker protection
"""

# import os  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
# import hashlib  # Moved to function to avoid circular import
# import socket  # Moved to function to avoid circular import
# import subprocess  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMKDF
# import base64  # Moved to function to avoid circular import
# import win32security  # Moved to function to avoid circular import
# import win32api  # Moved to function to avoid circular import
# import win32con  # Moved to function to avoid circular import

class SecurityManager:
    """Enterprise security manager"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_key = None
        self.authorized_chat_id = None
        self.firewall_rules = []
        self.security_log = []
        
        # Security configuration
        self.exness_servers = [
            '185.8.212.0/22',    # Primary data center
            '185.97.12.0/22',     # Backup data center
            '95.173.184.0/22',    # European servers
            '104.21.16.0/22',     # Cloudflare CDN
            '172.67.160.0/22',    # Cloudflare CDN
        ]
        
        # Initialize security
        self._initialize_security()
    
    def _initialize_security(self):
        """Initialize security systems"""
        try:
            # Generate encryption key
            self.encryption_key = self._generate_encryption_key()
            
            # Setup firewall
            self._setup_firewall()
            
            # Setup Windows security policies
            self._setup_windows_security()
            
            self.logger.info("✅ Security manager initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing security: {e}")
    
    def _generate_encryption_key(self) -> bytes:
        """Generate AES-256 encryption key"""
        try:
            # Get machine-specific entropy
            machine_entropy = f"{socket.gethostname()}{os.getpid()}{datetime.now().isoformat()}"
            
            # Use PBKDF2HMAC for key derivation
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=machine_entropy.encode(),
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(b"UOTA_ELITE_V2_SECURITY_KEY"))
            return key
            
        except Exception as e:
            self.logger.error(f"❌ Error generating encryption key: {e}")
            return Fernet.generate_key()
    
    def encrypt_credentials(self, credentials: Dict[str, str]) -> str:
        """Encrypt Exness credentials"""
        try:
            fernet = Fernet(self.encryption_key)
            
            # Convert credentials to JSON
            credentials_json = json.dumps(credentials)
            
            # Encrypt
            encrypted_data = fernet.encrypt(credentials_json.encode())
            
            # Save encrypted file
            encrypted_file = "data/credentials.encrypted"
            os.makedirs("data", exist_ok=True)
            
            with open(encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            
            self.logger.info("✅ Credentials encrypted successfully")
            return encrypted_file
            
        except Exception as e:
            self.logger.error(f"❌ Error encrypting credentials: {e}")
            return ""
    
    def decrypt_credentials(self) -> Optional[Dict[str, str]]:
        """Decrypt Exness credentials"""
        try:
            encrypted_file = "data/credentials.encrypted"
            
            if not os.path.exists(encrypted_file):
                self.logger.error("❌ Encrypted credentials file not found")
                return None
            
            fernet = Fernet(self.encryption_key)
            
            with open(encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Parse JSON
            credentials = json.loads(decrypted_data.decode())
            
            self.logger.info("✅ Credentials decrypted successfully")
            return credentials
            
        except Exception as e:
            self.logger.error(f"❌ Error decrypting credentials: {e}")
            return None
    
    def _setup_firewall(self):
        """Setup Windows firewall rules"""
        try:
            self.logger.info("🛡️ Setting up firewall rules...")
            
            # Clear existing rules
            self.firewall_rules.clear()
            
            # Add Exness server rules
            for server_range in self.exness_servers:
                rule = {
                    'action': 'allow',
                    'destination': server_range,
                    'protocol': 'tcp',
                    'ports': '443,1950,1951',
                    'description': f'Exness server: {server_range}'
                }
                self.firewall_rules.append(rule)
            
            # Add default deny rule
            deny_rule = {
                'action': 'deny',
                'destination': '0.0.0.0/0',
                'protocol': 'any',
                'description': 'Deny all other traffic'
            }
            self.firewall_rules.append(deny_rule)
            
            # Apply Windows firewall rules
            self._apply_windows_firewall()
            
            self.logger.info(f"✅ Firewall configured with {len(self.firewall_rules)} rules")
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up firewall: {e}")
    
    def _apply_windows_firewall(self):
        """Apply Windows firewall rules"""
        try:
            # Remove existing rules
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'delete', 'rule', 'name="UOTA Elite v2"'], 
                          capture_output=True, check=False)
            
            # Add Exness server rules
            for rule in self.firewall_rules:
                if rule['action'] == 'allow':
                    cmd = [
                        'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                        f'name="UOTA Elite v2 - {rule["description"]}"',
                        'dir=out', 'action=allow',
                        f'remoteip={rule["destination"]}',
                        f'protocol={rule["protocol"]}',
                        f'localport={rule["ports"]}',
                        'enable=yes'
                    ]
                    
                    subprocess.run(cmd, capture_output=True, check=False)
            
            self.logger.info("✅ Windows firewall rules applied")
            
        except Exception as e:
            self.logger.error(f"❌ Error applying Windows firewall: {e}")
    
    def _setup_windows_security(self):
        """Setup Windows security policies"""
        try:
            # Set file permissions for sensitive files
            sensitive_files = [
                "data/credentials.encrypted",
                ".env",
                "config.py"
            ]
            
            for file_path in sensitive_files:
                if os.path.exists(file_path):
                    # Restrict access to current user only
                    try:
                        # Get current user SID
                        user_sid = win32security.GetTokenInformation(
                            win32security.OpenProcessToken(win32api.GetCurrentProcess(), 
                                                         win32security.TOKEN_QUERY),
                            win32security.TokenUser
                        )[0]
                        
                        # Set file security
                        security_descriptor = win32security.SECURITY_DESCRIPTOR()
                        security_descriptor.SetSecurityDescriptorOwner(user_sid, False)
                        
                        # Apply to file
                        win32security.SetFileSecurity(file_path, win32security.DACL_SECURITY_INFORMATION, 
                                                     security_descriptor)
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not set permissions for {file_path}: {e}")
            
            # Disable unnecessary services
            unnecessary_services = ['Telnet', 'RemoteRegistry', 'PrintSpooler']
            
            for service in unnecessary_services:
                try:
                    subprocess.run(['sc', 'config', service, 'start=disabled'], 
                                  capture_output=True, check=False)
                    subprocess.run(['sc', 'stop', service], capture_output=True, check=False)
                except:
                    pass
            
            self.logger.info("✅ Windows security policies applied")
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up Windows security: {e}")
    
    def validate_telegram_access(self, chat_id: str) -> bool:
        """Validate Telegram access"""
        try:
            # Load authorized chat ID
            if not self.authorized_chat_id:
                credentials = self.decrypt_credentials()
                if credentials:
                    self.authorized_chat_id = credentials.get('TELEGRAM_CHAT_ID')
            
            if not self.authorized_chat_id:
                self.logger.error("❌ No authorized chat ID configured")
                return False
            
            # Validate chat ID
            is_authorized = str(chat_id) == str(self.authorized_chat_id)
            
            if not is_authorized:
                # Log unauthorized access attempt
                self._log_security_event('UNAUTHORIZED_TELEGRAM_ACCESS', {
                    'chat_id': chat_id,
                    'timestamp': datetime.now().isoformat(),
                    'authorized_chat_id': self.authorized_chat_id
                })
                
                # Send alert
                self._send_security_alert(f"🚨 UNAUTHORIZED TELEGRAM ACCESS\nChat ID: {chat_id}")
            
            return is_authorized
            
        except Exception as e:
            self.logger.error(f"❌ Error validating Telegram access: {e}")
            return False
    
    def _log_security_event(self, event_type: str, details: Dict):
        """Log security event"""
        try:
            event = {
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                'details': details
            }
            
            self.security_log.append(event)
            
            # Keep only last 1000 events
            if len(self.security_log) > 1000:
                self.security_log = self.security_log[-1000:]
            
            # Save to file
            log_file = "logs/security.log"
            os.makedirs("logs", exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {event_type} - {json.dumps(details)}\n")
            
            self.logger.info(f"🔒 Security event logged: {event_type}")
            
        except Exception as e:
            self.logger.error(f"❌ Error logging security event: {e}")
    
    def _send_security_alert(self, message: str):
        """Send security alert via Telegram"""
        try:
            from telegram_notifications import telegram_notifier
            
            alert_message = f"""
🚨 **SECURITY ALERT**
═════════════════════════════════════
{message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: 🚨 ALERT
"""
            
            asyncio.create_task(telegram_notifier.send_message(alert_message))
            
        except Exception as e:
            self.logger.error(f"❌ Error sending security alert: {e}")
    
    def validate_connection(self, host: str, port: int) -> bool:
        """Validate connection against firewall"""
        try:
            # Get IP address
            ip_address = socket.gethostbyname(host)
            
            # Check against whitelist
            for rule in self.firewall_rules:
                if rule['action'] == 'allow':
                    if self._ip_in_range(ip_address, rule['destination']):
                        return True
            
            # Log connection attempt
            self._log_security_event('CONNECTION_VALIDATION_FAILED', {
                'host': host,
                'ip': ip_address,
                'port': port,
                'timestamp': datetime.now().isoformat()
            })
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error validating connection: {e}")
            return False
    
    def _ip_in_range(self, ip: str, cidr: str) -> bool:
        """Check if IP is in CIDR range"""
        try:
            # import ipaddress  # Moved to function to avoid circular import
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr)
        except:
            return False
    
    def get_security_status(self) -> Dict:
        """Get security status"""
        return {
            'encryption_enabled': bool(self.encryption_key),
            'firewall_rules': len(self.firewall_rules),
            'authorized_chat_id': bool(self.authorized_chat_id),
            'security_events': len(self.security_log),
            'exness_servers': len(self.exness_servers),
            'last_security_check': datetime.now().isoformat()
        }
    
    def harden_system(self):
        """Apply comprehensive system hardening"""
        try:
            self.logger.info("🛡️ Starting system hardening...")
            
            # 1. Disable unnecessary services
            self._setup_windows_security()
            
            # 2. Set up firewall
            self._setup_firewall()
            
            # 3. Encrypt sensitive files
            credentials = {
                'EXNESS_LOGIN': os.environ.get('EXNESS_LOGIN', ''),
                'EXNESS_PASSWORD': os.environ.get('EXNESS_PASSWORD', ''),
                'EXNESS_SERVER': os.environ.get('EXNESS_SERVER', ''),
                'TELEGRAM_BOT_TOKEN': os.environ.get('TELEGRAM_BOT_TOKEN', ''),
                'TELEGRAM_CHAT_ID': os.environ.get('TELEGRAM_CHAT_ID', '')
            }
            
            self.encrypt_credentials(credentials)
            
            # 4. Set up process security
            self._setup_process_security()
            
            self.logger.info("✅ System hardening complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error in system hardening: {e}")
    
    def _setup_process_security(self):
        """Setup process-level security"""
        try:
            # Set process priority to high
            # import psutil  # Moved to function to avoid circular import
            process = psutil.Process()
            process.nice(psutil.HIGH_PRIORITY_CLASS)
            
            # Set process affinity to all cores
            process.cpu_affinity(list(range(psutil.cpu_count())))
            
            self.logger.info("✅ Process security configured")
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up process security: {e}")

# Global security manager instance
security_manager = SecurityManager()
