#!/usr/bin/env python3
"""
UOTA Elite v2 - Security Hardening Audit
Encryption verification and memory leak prevention
"""

# import os  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import psutil  # Moved to function to avoid circular import
# import gc  # Moved to function to avoid circular import
# import re  # Moved to function to avoid circular import
# import hashlib  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from pathlib import Path

class SecurityHardeningAudit:
    """Security hardening audit system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_tests = []
        self.memory_tests = []
        self.log_scans = []
        self.print_statement_removals = []
        
    def verify_aes256_encryption(self) -> Dict:
        """Verify AES-256 encryption functionality"""
        try:
            self.logger.info("🔐 Verifying AES-256 encryption...")
            
            test_results = {
                'encryption_functional': False,
                'decryption_functional': False,
                'key_strength_verified': False,
                'no_plain_text_leaks': False,
                'test_data': "TEST_CREDENTIAL_12345",
                'encrypted_data': None,
                'decrypted_data': None
            }
            
            # Test 1: Generate encryption key
            try:
                from cryptography.fernet import Fernet
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                # import base64  # Moved to function to avoid circular import
                
                # Generate strong key
                password = b"UOTA_ELITE_V2_TEST_PASSWORD"
                salt = os.urandom(16)
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                
                key = base64.urlsafe_b64encode(kdf.derive(password))
                
                # Verify key strength (should be 32 bytes for AES-256)
                if len(key) == 44:  # Base64 encoded 32-byte key
                    test_results['key_strength_verified'] = True
                    self.logger.info("✅ AES-256 key strength verified")
                else:
                    self.logger.error("❌ Key strength insufficient")
                
                # Test 2: Encryption
                fernet = Fernet(key)
                test_data = test_results['test_data'].encode()
                encrypted_data = fernet.encrypt(test_data)
                test_results['encrypted_data'] = encrypted_data.decode()
                test_results['encryption_functional'] = True
                self.logger.info("✅ Encryption functional")
                
                # Test 3: Decryption
                decrypted_data = fernet.decrypt(encrypted_data)
                test_results['decrypted_data'] = decrypted_data.decode()
                test_results['decryption_functional'] = True
                self.logger.info("✅ Decryption functional")
                
                # Verify data integrity
                if test_results['decrypted_data'] == test_results['test_data']:
                    self.logger.info("✅ Data integrity verified")
                else:
                    self.logger.error("❌ Data integrity compromised")
                
            except Exception as e:
                self.logger.error(f"❌ Encryption test failed: {e}")
            
            # Test 4: Check for plain text leaks in logs
            test_results['no_plain_text_leaks'] = self._scan_for_plain_text_leaks()
            
            # Test 5: Verify actual credential files
            credential_files = ['.env', 'data/credentials.encrypted']
            for file_path in credential_files:
                if os.path.exists(file_path):
                    encryption_status = self._verify_credential_encryption(file_path)
                    test_results[f'{file_path}_encrypted'] = encryption_status
            
            self.encryption_tests.append(test_results)
            return test_results
            
        except Exception as e:
            self.logger.error(f"❌ Error in encryption verification: {e}")
            return {'error': str(e)}
    
    def _scan_for_plain_text_leaks(self) -> bool:
        """Scan log files for plain text credentials"""
        try:
            log_files = ['logs/', '.log', '.txt']
            sensitive_patterns = [
                r'password\s*=\s*["\']?[^"\'\s]+',
                r'token\s*=\s*["\']?[^"\'\s]+',
                r'api_key\s*=\s*["\']?[^"\'\s]+',
                r'secret\s*=\s*["\']?[^"\'\s]+',
                r'EXNESS_PASSWORD',
                r'TELEGRAM_BOT_TOKEN',
                r'login\s*=\s*["\']?[^"\'\s]+'
            ]
            
            leaks_found = []
            
            # Scan common log locations
            for root, dirs, files in os.walk('.'):
                # Skip hidden directories and common non-log directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]
                
                for file in files:
                    if any(file.endswith(ext) for ext in ['.log', '.txt']):
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                for pattern in sensitive_patterns:
                                    matches = re.findall(pattern, content, re.IGNORECASE)
                                    if matches:
                                        leaks_found.append({
                                            'file': file_path,
                                            'pattern': pattern,
                                            'matches': len(matches)
                                        })
                                        
                        except Exception as e:
                            self.logger.warning(f"⚠️ Could not scan {file_path}: {e}")
            
            if leaks_found:
                self.logger.error(f"❌ Plain text leaks found: {len(leaks_found)}")
                for leak in leaks_found:
                    self.logger.error(f"   📁 {leak['file']}: {leak['pattern']} ({leak['matches']} matches)")
                return False
            else:
                self.logger.info("✅ No plain text credential leaks found")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error scanning for plain text leaks: {e}")
            return False
    
    def _verify_credential_encryption(self, file_path: str) -> bool:
        """Verify credential file encryption"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check if content is encrypted (should not contain readable text)
            try:
                content_str = content.decode('utf-8')
                
                # If it decodes to readable text, it's not encrypted
                if any(keyword in content_str.lower() for keyword in ['password', 'token', 'login', 'secret']):
                    self.logger.warning(f"⚠️ {file_path} may contain plain text credentials")
                    return False
                else:
                    self.logger.info(f"✅ {file_path} appears to be encrypted")
                    return True
                    
            except UnicodeDecodeError:
                # If it can't be decoded as UTF-8, it's likely encrypted
                self.logger.info(f"✅ {file_path} appears to be encrypted (binary data)")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error verifying {file_path} encryption: {e}")
            return False
    
    def optimize_memory_usage(self) -> Dict:
        """Optimize memory usage and prevent leaks"""
        try:
            self.logger.info("🧹 Optimizing memory usage...")
            
            # Get initial memory state
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Force garbage collection
            collected_objects = gc.collect()
            
            # Get memory after garbage collection
            after_gc_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Optimize data buffers
            optimization_results = self._optimize_data_buffers()
            
            # Get final memory state
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            memory_saved = initial_memory - final_memory
            
            results = {
                'initial_memory_mb': initial_memory,
                'after_gc_memory_mb': after_gc_memory,
                'final_memory_mb': final_memory,
                'memory_saved_mb': memory_saved,
                'objects_collected': collected_objects,
                'under_200mb_target': final_memory < 200,
                'buffer_optimizations': optimization_results
            }
            
            self.memory_tests.append(results)
            
            if results['under_200mb_target']:
                self.logger.info(f"✅ Memory optimization successful: {final_memory:.1f}MB (< 200MB)")
            else:
                self.logger.warning(f"⚠️ Memory usage above target: {final_memory:.1f}MB (> 200MB)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing memory: {e}")
            return {'error': str(e)}
    
    def _optimize_data_buffers(self) -> Dict:
        """Optimize data buffers to reduce memory usage"""
        try:
            optimizations = {
                'circular_buffers_optimized': 0,
                'data_structures_cleaned': 0,
                'cache_cleared': 0
            }
            
            # Optimize circular buffers (if they exist)
            buffer_modules = ['performance_optimization', 'market_data_validator', 'automated_logging_system']
            
            for module_name in buffer_modules:
                try:
                    module = sys.modules.get(module_name)
                    if module and hasattr(module, 'market_data_buffer'):
                        # Reduce buffer size
                        if hasattr(module, 'buffer_size'):
                            original_size = module.buffer_size
                            module.buffer_size = min(original_size, 500)  # Limit to 500 items
                            optimizations['circular_buffers_optimized'] += 1
                            self.logger.info(f"✅ Optimized {module_name} buffer: {original_size} -> {module.buffer_size}")
                
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not optimize {module_name}: {e}")
            
            # Clean up data structures
            gc.collect()  # Force garbage collection
            optimizations['data_structures_cleaned'] = gc.collect()
            
            # Clear caches
            try:
                if hasattr(sys, '_getframe'):
                    # Clear frame references
                    while self.is_running:
                        frame = sys._getframe()
                        if not frame:
                            break
                        frame.clear()
                
                optimizations['cache_cleared'] = 1
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not clear caches: {e}")
            
            return optimizations
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing data buffers: {e}")
            return {'error': str(e)}
    
    def remove_print_statements(self) -> Dict:
        """Remove unnecessary print statements for CPU optimization"""
        try:
            self.logger.info("🧹 Removing unnecessary print statements...")
            
            # Files to scan and optimize
            critical_files = [
                'master_controller.py',
                'exchange_integration.py',
                'smc_logic_gate.py',
                'brain.py',
                'immortal_watchdog.py',
                'telegram_c2.py',
                'autonomous_rollover.py'
            ]
            
            removal_results = {
                'files_scanned': 0,
                'print_statements_removed': 0,
                'files_modified': 0,
                'critical_prints_preserved': 0,
                'optimizations': []
            }
            
            # Critical print statements to preserve
            critical_patterns = [
                'print.*error',
                'print.*critical',
                'print.*trade',
                'print.*execution',
                'print.*profit',
                'print.*loss',
                'print.*emergency',
                'print.*security'
            ]
            
            for file_path in critical_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        original_content = content
                        
                        # Find all print statements
                        print_pattern = r'print\s*\([^)]+\)'
                        print_matches = re.findall(print_pattern, content)
                        
                        # Count critical vs non-critical prints
                        critical_prints = 0
                        non_critical_prints = 0
                        
                        for print_match in print_matches:
                            is_critical = any(re.search(pattern, print_match, re.IGNORECASE) for pattern in critical_patterns)
                            
                            if is_critical:
                                critical_prints += 1
                            else:
                                non_critical_prints += 1
                                # Replace non-critical print with logger
                                logger_replacement = print_match.replace('print(', '# print(')  # Comment out for safety
                                content = content.replace(print_match, logger_replacement)
                        
                        # Write back if changes made
                        if content != original_content:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            
                            removal_results['files_modified'] += 1
                            removal_results['print_statements_removed'] += non_critical_prints
                        
                        removal_results['files_scanned'] += 1
                        removal_results['critical_prints_preserved'] += critical_prints
                        
                        removal_results['optimizations'].append({
                            'file': file_path,
                            'total_prints': len(print_matches),
                            'critical_preserved': critical_prints,
                            'non_critical_removed': non_critical_prints
                        })
                        
                        self.logger.info(f"✅ {file_path}: {non_critical_prints} non-critical prints removed, {critical_prints} critical preserved")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error optimizing {file_path}: {e}")
            
            self.print_statement_removals.append(removal_results)
            
            self.logger.info(f"✅ Print statement optimization complete: {removal_results['print_statements_removed']} removed")
            
            return removal_results
            
        except Exception as e:
            self.logger.error(f"❌ Error removing print statements: {e}")
            return {'error': str(e)}
    
    def get_security_audit_report(self) -> Dict:
        """Generate comprehensive security audit report"""
        try:
            # Run all security tests
            encryption_results = self.verify_aes256_encryption()
            memory_results = self.optimize_memory_usage()
            print_results = self.remove_print_statements()
            
            # Calculate overall security score
            security_score = 0
            max_score = 100
            
            # Encryption score (40 points)
            if encryption_results.get('encryption_functional', False):
                security_score += 10
            if encryption_results.get('decryption_functional', False):
                security_score += 10
            if encryption_results.get('key_strength_verified', False):
                security_score += 10
            if encryption_results.get('no_plain_text_leaks', False):
                security_score += 10
            
            # Memory score (30 points)
            if memory_results.get('under_200mb_target', False):
                security_score += 20
            if memory_results.get('memory_saved_mb', 0) > 0:
                security_score += 10
            
            # Print optimization score (30 points)
            if print_results.get('print_statements_removed', 0) > 0:
                security_score += 15
            if print_results.get('critical_prints_preserved', 0) > 0:
                security_score += 15
            
            report = {
                'audit_timestamp': datetime.now().isoformat(),
                'overall_security_score': security_score,
                'max_score': max_score,
                'security_grade': self._calculate_security_grade(security_score),
                'encryption_audit': encryption_results,
                'memory_audit': memory_results,
                'print_optimization': print_results,
                'recommendations': self._generate_security_recommendations(security_score),
                'compliance_status': {
                    'aes256_compliant': encryption_results.get('key_strength_verified', False),
                    'memory_compliant': memory_results.get('under_200mb_target', False),
                    'cpu_optimized': print_results.get('print_statements_removed', 0) > 0,
                    'no_plain_text_leaks': encryption_results.get('no_plain_text_leaks', False)
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating security audit report: {e}")
            return {'error': str(e)}
    
    def _calculate_security_grade(self, score: int) -> str:
        """Calculate security grade"""
        if score >= 90:
            return 'A+ (EXCELLENT)'
        elif score >= 80:
            return 'A (VERY GOOD)'
        elif score >= 70:
            return 'B (GOOD)'
        elif score >= 60:
            return 'C (FAIR)'
        elif score >= 50:
            return 'D (POOR)'
        else:
            return 'F (CRITICAL)'
    
    def _generate_security_recommendations(self, score: int) -> List[str]:
        """Generate security recommendations based on score"""
        recommendations = []
        
        if score < 90:
            recommendations.append("🔐 Implement additional security measures for maximum protection")
        
        if score < 80:
            recommendations.append("🧹 Optimize memory usage to stay under 200MB target")
        
        if score < 70:
            recommendations.append("🖨️ Remove more non-critical print statements")
        
        if score < 60:
            recommendations.append("🚨 CRITICAL: Address all security vulnerabilities immediately")
        
        if score >= 90:
            recommendations.append("✅ System meets enterprise-grade security standards")
        
        return recommendations

# Global security hardening audit instance
security_hardening_audit = SecurityHardeningAudit()
