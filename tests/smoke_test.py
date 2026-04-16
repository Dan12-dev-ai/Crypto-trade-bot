#!/usr/bin/env python3
"""
UOTA Elite v2 - Smoke Test Script
Quick health check for the entire swarm system
"""

import asyncio
import logging
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SmokeTestResult:
    """Smoke test result"""
    def __init__(self, component: str, status: str, message: str, execution_time: float):
        self.component = component
        self.status = status  # PASS, FAIL, WARN
        self.message = message
        self.execution_time = execution_time
        self.timestamp = datetime.now()

class SmokeTestSuite:
    """Quick health check suite"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results = []
        self.start_time = datetime.now()
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests"""
        print("UOTA Elite v2 - Smoke Test Suite")
        print("=" * 50)
        
        # Test 1: System Files Check
        await self.test_system_files()
        
        # Test 2: Configuration Check
        await self.test_configuration()
        
        # Test 3: Dependencies Check
        await self.test_dependencies()
        
        # Test 4: Security Check
        await self.test_security()
        
        # Test 5: Memory System Check
        await self.test_memory_system()
        
        # Test 6: Consensus Engine Check
        await self.test_consensus_engine()
        
        # Test 7: Digital Twin Check
        await self.test_digital_twin()
        
        # Test 8: Research Lab Check
        await self.test_research_lab()
        
        # Test 9: Orchestrator Check
        await self.test_orchestrator()
        
        # Test 10: Deployment Check
        await self.test_deployment()
        
        # Generate summary
        return self.generate_summary()
    
    async def test_system_files(self) -> None:
        """Test 1: System Files Check"""
        start_time = time.time()
        component = "System Files"
        
        try:
            required_files = [
                'main_orchestrator.py',
                'memory/vector_store.py',
                'simulation/digital_twin.py',
                'research/autonomous_research.py',
                'execution/consensus_engine.py',
                'security/ip_validator.py',
                'docker-compose.elite.yml',
                'koyeb_config.yml',
                'project_structure.md'
            ]
            
            missing_files = []
            for file_path in required_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                status = "FAIL"
                message = f"Missing files: {missing_files}"
            else:
                status = "PASS"
                message = f"All {len(required_files)} required files present"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    async def test_configuration(self) -> None:
        """Test 2: Configuration Check"""
        start_time = time.time()
        component = "Configuration"
        
        try:
            # Check for config.py
            if not Path('config.py').exists():
                result = SmokeTestResult(component, "FAIL", "config.py not found", time.time() - start_time)
                self.results.append(result)
                print(f"[FAIL] {component}: config.py not found")
                return
            
            # Check environment variables
            env_vars = [
                'EXCHANGE_API_KEY',
                'TELEGRAM_BOT_TOKEN',
                'POSTGRES_PASSWORD',
                'RABBITMQ_USER',
                'RABBITMQ_PASSWORD'
            ]
            
            missing_vars = []
            for var in env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                status = "WARN"
                message = f"Missing env vars: {missing_vars}"
            else:
                status = "PASS"
                message = "All required environment variables set"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    async def test_dependencies(self) -> None:
        """Test 3: Dependencies Check"""
        start_time = time.time()
        component = "Dependencies"
        
        try:
            required_packages = [
                'asyncio',
                'logging',
                'json',
                'datetime',
                'pathlib',
                'typing',
                'dataclasses',
                'enum'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            # Check for optional packages
            optional_packages = ['chromadb', 'langgraph', 'crewai', 'pandas', 'numpy']
            available_optional = []
            for package in optional_packages:
                try:
                    __import__(package)
                    available_optional.append(package)
                except ImportError:
                    pass
            
            if missing_packages:
                status = "FAIL"
                message = f"Missing required packages: {missing_packages}"
            elif len(available_optional) < len(optional_packages) * 0.5:
                status = "WARN"
                message = f"Only {len(available_optional)}/{len(optional_packages)} optional packages available"
            else:
                status = "PASS"
                message = f"All required packages available, {len(available_optional)} optional packages"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    async def test_security(self) -> None:
        """Test 4: Security Check"""
        start_time = time.time()
        component = "Security"
        
        try:
            # Check if security module exists
            if not Path('security/ip_validator.py').exists():
                result = SmokeTestResult(component, "FAIL", "Security module not found", time.time() - start_time)
                self.results.append(result)
                print(f"[FAIL] {component}: Security module not found")
                return
            
            # Check security directories
            security_dirs = ['data/security']
            missing_dirs = []
            for dir_path in security_dirs:
                if not Path(dir_path).exists():
                    missing_dirs.append(dir_path)
            
            # Check file permissions
            sensitive_files = ['.env', 'config/credentials.json']
            insecure_files = []
            for file_path in sensitive_files:
                if Path(file_path).exists():
                    stat = Path(file_path).stat()
                    if stat.st_mode & 0o077:  # Check if others have read/write access
                        insecure_files.append(file_path)
            
            if insecure_files:
                status = "WARN"
                message = f"Insecure file permissions: {insecure_files}"
            elif missing_dirs:
                status = "WARN"
                message = f"Missing security directories: {missing_dirs}"
            else:
                status = "PASS"
                message = "Security configuration OK"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    async def test_memory_system(self) -> None:
        """Test 5: Memory System Check"""
        start_time = time.time()
        component = "Memory System"
        
        try:
            # Check if memory module exists
            if not Path('memory/vector_store.py').exists():
                result = SmokeTestResult(component, "FAIL", "Memory module not found", time.time() - start_time)
                self.results.append(result)
                print(f"[FAIL] {component}: Memory module not found")
                return
            
            # Check memory directories
            memory_dirs = ['data/vector_memory', 'memory']
            missing_dirs = []
            for dir_path in memory_dirs:
                if not Path(dir_path).exists():
                    missing_dirs.append(dir_path)
            
            # Try to import the module (basic syntax check)
            try:
                sys.path.append('memory')
                import vector_store
                syntax_ok = True
            except Exception as e:
                syntax_ok = False
                import_error = str(e)
            
            if not syntax_ok:
                status = "FAIL"
                message = f"Syntax error in memory module: {import_error}"
            elif missing_dirs:
                status = "WARN"
                message = f"Missing memory directories: {missing_dirs}"
            else:
                status = "PASS"
                message = "Memory system OK"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    async def test_consensus_engine(self) -> None:
        """Test 6: Consensus Engine Check"""
        start_time = time.time()
        component = "Consensus Engine"
        
        try:
            # Check if consensus module exists
            if not Path('execution/consensus_engine.py').exists():
                result = SmokeTestResult(component, "FAIL", "Consensus engine not found", time.time() - start_time)
                self.results.append(result)
                print(f"[FAIL] {component}: Consensus engine not found")
                return
            
            # Try to import the module
            try:
                sys.path.append('execution')
                import consensus_engine
                syntax_ok = True
            except Exception as e:
                syntax_ok = False
                import_error = str(e)
            
            if not syntax_ok:
                status = "FAIL"
                message = f"Syntax error in consensus engine: {import_error}"
            else:
                status = "PASS"
                message = "Consensus engine OK"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    async def test_digital_twin(self) -> None:
        """Test 7: Digital Twin Check"""
        start_time = time.time()
        component = "Digital Twin"
        
        try:
            # Check if digital twin module exists
            if not Path('simulation/digital_twin.py').exists():
                result = SmokeTestResult(component, "FAIL", "Digital twin not found", time.time() - start_time)
                self.results.append(result)
                print(f"[FAIL] {component}: Digital twin not found")
                return
            
            # Try to import the module
            try:
                sys.path.append('simulation')
                import digital_twin
                syntax_ok = True
            except Exception as e:
                syntax_ok = False
                import_error = str(e)
            
            if not syntax_ok:
                status = "FAIL"
                message = f"Syntax error in digital twin: {import_error}"
            else:
                status = "PASS"
                message = "Digital twin OK"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    async def test_research_lab(self) -> None:
        """Test 8: Research Lab Check"""
        start_time = time.time()
        component = "Research Lab"
        
        try:
            # Check if research lab module exists
            if not Path('research/autonomous_research.py').exists():
                result = SmokeTestResult(component, "FAIL", "Research lab not found", time.time() - start_time)
                self.results.append(result)
                print(f"[FAIL] {component}: Research lab not found")
                return
            
            # Try to import the module
            try:
                sys.path.append('research')
                import autonomous_research
                syntax_ok = True
            except Exception as e:
                syntax_ok = False
                import_error = str(e)
            
            if not syntax_ok:
                status = "FAIL"
                message = f"Syntax error in research lab: {import_error}"
            else:
                status = "PASS"
                message = "Research lab OK"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    async def test_orchestrator(self) -> None:
        """Test 9: Orchestrator Check"""
        start_time = time.time()
        component = "Orchestrator"
        
        try:
            # Check if orchestrator module exists
            if not Path('main_orchestrator.py').exists():
                result = SmokeTestResult(component, "FAIL", "Orchestrator not found", time.time() - start_time)
                self.results.append(result)
                print(f"[FAIL] {component}: Orchestrator not found")
                return
            
            # Try to import the module
            try:
                import main_orchestrator
                syntax_ok = True
            except Exception as e:
                syntax_ok = False
                import_error = str(e)
            
            if not syntax_ok:
                status = "FAIL"
                message = f"Syntax error in orchestrator: {import_error}"
            else:
                status = "PASS"
                message = "Orchestrator OK"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    async def test_deployment(self) -> None:
        """Test 10: Deployment Check"""
        start_time = time.time()
        component = "Deployment"
        
        try:
            # Check deployment files
            deployment_files = [
                'docker-compose.elite.yml',
                'koyeb_config.yml'
            ]
            
            missing_files = []
            for file_path in deployment_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            # Check Docker installation
            docker_available = False
            try:
                result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    docker_available = True
            except:
                pass
            
            if missing_files:
                status = "WARN"
                message = f"Missing deployment files: {missing_files}"
            elif not docker_available:
                status = "WARN"
                message = "Docker not available"
            else:
                status = "PASS"
                message = "Deployment configuration OK"
            
            result = SmokeTestResult(component, status, message, time.time() - start_time)
            self.results.append(result)
            print(f"[{status}] {component}: {message}")
            
        except Exception as e:
            result = SmokeTestResult(component, "FAIL", f"Error: {str(e)}", time.time() - start_time)
            self.results.append(result)
            print(f"[FAIL] {component}: {str(e)}")
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(self.results)
        passed = len([r for r in self.results if r.status == "PASS"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        warnings = len([r for r in self.results if r.status == "WARN"])
        
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * 50)
        print("SMOKE TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Warnings: {warnings}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        print(f"Execution Time: {execution_time:.2f}s")
        print("=" * 50)
        
        # Overall status
        if failed > 0:
            overall_status = "CRITICAL"
        elif warnings > 0:
            overall_status = "WARNING"
        else:
            overall_status = "HEALTHY"
        
        print(f"Overall System Status: {overall_status}")
        print("=" * 50)
        
        return {
            'overall_status': overall_status,
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'success_rate': (passed/total_tests)*100,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'results': [
                {
                    'component': r.component,
                    'status': r.status,
                    'message': r.message,
                    'execution_time': r.execution_time,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }

async def main():
    """Main smoke test execution"""
    smoke_test = SmokeTestSuite()
    
    try:
        results = await smoke_test.run_all_tests()
        
        # Save results to file
        with open('smoke_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: smoke_test_results.json")
        
        # Exit with appropriate code
        if results['failed'] > 0:
            sys.exit(1)
        elif results['warnings'] > 0:
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Smoke test failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())
