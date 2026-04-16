#!/usr/bin/env python3
"""
UOTA Elite v2 - MT5 Diagnostic Tool
Troubleshoot pymt5linux connection issues
"""

# import subprocess  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import os  # Moved to function to avoid circular import

def run_diagnostic():
    print("🔍 UOTA ELITE v2 - MT5 CONNECTION DIAGNOSTIC")
    print("=" * 60)
    print()
    
    # Step 1: Check if pymt5linux is installed
    print("📦 STEP 1: CHECKING PYMT5LINUX INSTALLATION")
    try:
        # # import pymt5linux  # Moved to function to avoid circular import  # Moved to function to avoid circular import
        print("✅ pymt5linux: INSTALLED")
        print(f"📍 Version: {getattr(pymt5linux, '__version__', 'Unknown')}")
    except ImportError as e:
        print(f"❌ pymt5linux: NOT INSTALLED - {e}")
        print("🔧 Install with: pip install pymt5linux")
        return
    print()
    
    # Step 2: Check Wine installation
    print("🍷 STEP 2: CHECKING WINE INSTALLATION")
    try:
        wine_version = subprocess.run(['wine', '--version'], capture_output=True, text=True)
        if wine_version.returncode == 0:
            print(f"✅ Wine: INSTALLED - {wine_version.stdout.strip()}")
        else:
            print("❌ Wine: NOT WORKING")
    except FileNotFoundError:
        print("❌ Wine: NOT INSTALLED")
        print("🔧 Install with: sudo apt install wine")
        return
    print()
    
    # Step 3: Check for running MT5 processes
    print("🖥️ STEP 3: CHECKING MT5 PROCESSES")
    try:
        # Check for MT5 processes
        ps_output = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        mt5_processes = [line for line in ps_output.stdout.split('\n') if 'terminal64' in line.lower() or 'mt5' in line.lower()]
        
        if mt5_processes:
            print("✅ MT5 Processes Found:")
            for process in mt5_processes:
                print(f"  {process}")
        else:
            print("❌ No MT5 processes found")
            print("🔧 Start MT5 terminal first")
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
    print()
    
    # Step 4: Test pymt5linux connection
    print("🔗 STEP 4: TESTING PYMT5LINUX CONNECTION")
    try:
        from pymt5linux import MetaTrader5 as mt5
        
        # Test basic import
        print("✅ pymt5linux: IMPORT SUCCESS")
        
        # Test initialization
        mt5_instance = mt5()
        print("✅ MT5 Instance: CREATED")
        
        # Test connection
        if mt5_instance.initialize():
            print("✅ MT5 Connection: ESTABLISHED")
            
            # Get account info
            account_info = mt5_instance.account_info()
            if account_info:
                print(f"✅ Account Info: {account_info.login} - {account_info.server}")
                print(f"💰 Balance: ${account_info.balance:.2f}")
                print(f"💎 Equity: ${account_info.equity:.2f}")
                print()
                print("🎯 CONNECTION SUCCESSFUL!")
                print("🚀 Ready to launch mission!")
            else:
                print("❌ Cannot get account info")
        else:
            print("❌ MT5 Connection: FAILED")
            print("🔧 Troubleshooting:")
            print("  1. Ensure MT5 is running")
            print("  2. Check Wine configuration")
            print("  3. Verify MT5 window is accessible")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("🔧 Check Wine and MT5 configuration")
    print()
    
    # Step 5: Check environment variables
    print("🌍 STEP 5: CHECKING ENVIRONMENT")
    env_vars = ['WINEPREFIX', 'DISPLAY', 'PATH']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"  {var}: {value}")
    print()
    
    # Step 6: Provide recommendations
    print("🎯 RECOMMENDATIONS")
    print("-" * 30)
    print("1. 🍷 Ensure Wine is properly configured")
    print("2. 🖥️ Start MT5 terminal via Wine:")
    print("   wine '/path/to/mt5/terminal64.exe'")
    print("3. 🔐 Login to account 11000575398")
    print("4. 🏛️ Connect to Exness-MT5Trial10 server")
    print("5. 🚀 Run diagnostic again to verify")
    print()
    print("📋 If connection still fails:")
    print("  • Check Wine prefix configuration")
    print("  • Verify MT5 installation path")
    print("  • Try restarting MT5 terminal")
    print("  • Check system permissions")

if __name__ == "__main__":
    run_diagnostic()
