#!/usr/bin/env python3
"""
UOTA Elite v2 - Final Health Check
Quick system health verification
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

class FinalHealthCheck:
    """Final health check system"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.health_status = {
            'syntax_errors': 0,
            'missing_files': 0,
            'security_issues': 0,
            'performance_issues': 0,
            'overall_score': 0
        }
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/final_health.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def check_core_files(self):
        """Check core files exist and are valid"""
        try:
            self.logger.info("📁 Checking core files...")
            
            core_files = [
                'master_controller.py',
                'cloud_watchdog.py',
                'cloud_telegram_c2.py',
                'cloud_resilience.py',
                'cloud_deployment.py',
                'deploy_cloud_vps.bat',
                'requirements.txt',
                '.env'
            ]
            
            missing_files = []
            syntax_errors = []
            
            for file_path in core_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
                    self.health_status['missing_files'] += 1
                    self.logger.warning(f"❌ Missing file: {file_path}")
                elif file_path.endswith('.py'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Basic syntax check
                        compile(content, file_path, 'exec')
                        
                    except SyntaxError as e:
                        syntax_errors.append(f"{file_path}: {e}")
                        self.health_status['syntax_errors'] += 1
                        self.logger.error(f"❌ Syntax error in {file_path}: {e}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error checking {file_path}: {e}")
            
            return {
                'core_files_checked': len(core_files),
                'missing_files': missing_files,
                'syntax_errors': syntax_errors,
                'files_valid': len(core_files) - len(missing_files) - len(syntax_errors)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error checking core files: {e}")
            return {'error': str(e)}
    
    def check_security_configuration(self):
        """Check security configuration"""
        try:
            self.logger.info("🛡️ Checking security configuration...")
            
            security_check = {
                'env_file_exists': os.path.exists('.env'),
                'env_configured': False,
                'telegram_configured': False,
                'exness_configured': False,
                'security_issues': []
            }
            
            if security_check['env_file_exists']:
                with open('.env', 'r') as f:
                    env_content = f.read()
                
                if 'TELEGRAM_BOT_TOKEN=' in env_content and 'your_bot_token_here' not in env_content:
                    security_check['telegram_configured'] = True
                
                if 'TELEGRAM_CHAT_ID=' in env_content and 'your_chat_id_here' not in env_content:
                    security_check['telegram_configured'] = True
                
                if 'EXNESS_LOGIN=' in env_content and 'your_login_here' not in env_content:
                    security_check['exness_configured'] = True
                
                if security_check['telegram_configured'] and security_check['exness_configured']:
                    security_check['env_configured'] = True
                else:
                    security_check['security_issues'].append("Incomplete .env configuration")
                    self.health_status['security_issues'] += 1
            
            return security_check
            
        except Exception as e:
            self.logger.error(f"❌ Error checking security: {e}")
            return {'error': str(e)}
    
    def check_performance_requirements(self):
        """Check performance requirements"""
        try:
            self.logger.info("⚡ Checking performance requirements...")
            
            performance_check = {
                'python_version': sys.version_info,
                'python_compatible': sys.version_info >= (3, 8),
                'requirements_installed': False,
                'memory_available': True,
                'disk_space': True,
                'performance_issues': []
            }
            
            # Check Python version
            if not performance_check['python_compatible']:
                performance_check['performance_issues'].append("Python 3.8+ required")
                self.health_status['performance_issues'] += 1
            
            # Check requirements
            if os.path.exists('requirements.txt'):
                try:
                    import pkg_resources
                    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
                    
                    with open('requirements.txt', 'r') as f:
                        requirements = f.read()
                    
                    missing_packages = []
                    for line in requirements.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            package_name = line.split('>=')[0].split('==')[0].split('~=')[0].strip()
                            if package_name not in installed_packages:
                                missing_packages.append(package_name)
                    
                    if not missing_packages:
                        performance_check['requirements_installed'] = True
                    else:
                        performance_check['performance_issues'].append(f"Missing packages: {missing_packages}")
                        self.health_status['performance_issues'] += 1
                        
                except Exception as e:
                    performance_check['performance_issues'].append(f"Requirements check error: {e}")
                    self.health_status['performance_issues'] += 1
            
            # Check disk space
            import shutil
            total, used, free = shutil.disk_usage('.')
            if free < (1024**3):  # Less than 1GB free
                performance_check['performance_issues'].append("Low disk space")
                self.health_status['performance_issues'] += 1
                performance_check['disk_space'] = False
            
            return performance_check
            
        except Exception as e:
            self.logger.error(f"❌ Error checking performance: {e}")
            return {'error': str(e)}
    
    def calculate_overall_health(self, core_files, security, performance):
        """Calculate overall health score"""
        try:
            score = 100
            
            # Core files (40%)
            if core_files.get('files_valid', 0) < 7:
                score -= 40
            elif core_files.get('syntax_errors', 0) > 0:
                score -= 20
            
            # Security (30%)
            if not security.get('env_configured', False):
                score -= 30
            elif not security.get('telegram_configured', False):
                score -= 15
            
            # Performance (30%)
            if not performance.get('python_compatible', False):
                score -= 30
            elif not performance.get('requirements_installed', False):
                score -= 15
            
            self.health_status['overall_score'] = max(0, score)
            
            return self.health_status['overall_score']
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating health: {e}")
            return 0
    
    def generate_health_report(self):
        """Generate final health report"""
        try:
            self.logger.info("📊 Generating final health report...")
            
            # Run all checks
            core_files = self.check_core_files()
            security = self.check_security_configuration()
            performance = self.check_performance_requirements()
            
            # Calculate overall score
            overall_score = self.calculate_overall_health(core_files, security, performance)
            
            # Determine grade
            if overall_score >= 90:
                grade = 'A+ (EXCELLENT)'
            elif overall_score >= 80:
                grade = 'A (VERY GOOD)'
            elif overall_score >= 70:
                grade = 'B (GOOD)'
            elif overall_score >= 60:
                grade = 'C (FAIR)'
            else:
                grade = 'D (NEEDS IMPROVEMENT)'
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'overall_score': overall_score,
                'grade': grade,
                'ready_for_deployment': overall_score >= 80,
                'core_files': core_files,
                'security': security,
                'performance': performance,
                'recommendations': self._generate_recommendations(overall_score)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating report: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, score: int) -> list:
        """Generate recommendations based on score"""
        recommendations = []
        
        if score < 90:
            recommendations.append("🔧 Fix remaining syntax errors")
        
        if score < 80:
            recommendations.append("📦 Install missing dependencies")
        
        if score < 70:
            recommendations.append("🛡️ Complete security configuration")
        
        if score < 60:
            recommendations.append("📁 Restore missing core files")
        
        if score >= 80:
            recommendations.append("✅ System ready for cloud deployment")
        
        return recommendations
    
    def display_health_report(self, report: dict):
        """Display health report"""
        try:
            print("\n" + "=" * 80)
            print("🧪 UOTA ELITE v2 - FINAL HEALTH CHECK")
            print("=" * 80)
            
            print(f"\n📊 OVERALL HEALTH SCORE: {report['overall_score']}/100")
            print(f"🏆 HEALTH GRADE: {report['grade']}")
            print(f"🚀 DEPLOYMENT READY: {'✅ YES' if report['ready_for_deployment'] else '❌ NO'}")
            
            print(f"\n📁 CORE FILES:")
            core = report['core_files']
            print(f"   Files Checked: {core.get('core_files_checked', 0)}")
            print(f"   Files Valid: {core.get('files_valid', 0)}")
            print(f"   Missing Files: {len(core.get('missing_files', []))}")
            print(f"   Syntax Errors: {len(core.get('syntax_errors', []))}")
            
            print(f"\n🛡️ SECURITY:")
            sec = report['security']
            print(f"   .env File: {'✅ EXISTS' if sec.get('env_file_exists') else '❌ MISSING'}")
            print(f"   Configured: {'✅ YES' if sec.get('env_configured') else '❌ NO'}")
            print(f"   Telegram: {'✅ CONFIGURED' if sec.get('telegram_configured') else '❌ NOT CONFIGURED'}")
            print(f"   Exness: {'✅ CONFIGURED' if sec.get('exness_configured') else '❌ NOT CONFIGURED'}")
            
            print(f"\n⚡ PERFORMANCE:")
            perf = report['performance']
            print(f"   Python Version: {'✅ COMPATIBLE' if perf.get('python_compatible') else '❌ INCOMPATIBLE'}")
            print(f"   Requirements: {'✅ INSTALLED' if perf.get('requirements_installed') else '❌ MISSING'}")
            print(f"   Disk Space: {'✅ AVAILABLE' if perf.get('disk_space') else '❌ LOW'}")
            
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"   {rec}")
            
            print("\n" + "=" * 80)
            
            if report['ready_for_deployment']:
                print("🎯 SYSTEM HEALTH: EXCELLENT - Ready for 24/7 cloud deployment")
                print("🚀 Your UOTA Elite v2 is ready for production!")
            else:
                print("⚠️ SYSTEM HEALTH: NEEDS IMPROVEMENT - Address issues before deployment")
            
            print("=" * 80)
            
        except Exception as e:
            self.logger.error(f"❌ Error displaying report: {e}")

# Global health checker
final_health_check = FinalHealthCheck()

def main():
    """Main entry point"""
    print("🧪 Starting Final Health Check...")
    
    health_checker = final_health_check
    
    try:
        # Generate health report
        report = health_checker.generate_health_report()
        
        # Display report
        health_checker.display_health_report(report)
        
        # Save report
        with open('final_health_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Health report saved to: final_health_report.json")
        
    except Exception as e:
        print(f"❌ Fatal error in health check: {e}")

if __name__ == "__main__":
    main()
