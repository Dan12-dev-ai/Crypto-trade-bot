#!/usr/bin/env python3
"""
UOTA Elite v2 - MT5 Connection Status Checker
"""

# import asyncio  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import os  # Moved to function to avoid circular import

async def check_mt5_connection():
    try:
        print('🔗 Checking MT5 Connection Status...')
        print('=' * 50)
        
        # Import MT5 integration
        from mt5_integration # import mt5_integration  # Moved to function to avoid circular import
        
        # Initialize connection
        print('📡 Initializing MT5 connection...')
        connected = await mt5_integration.initialize()
        
        if connected:
            print('✅ MT5 Connection: ESTABLISHED')
            print()
            
            # Get account information
            account_info = await mt5_integration.get_account_balance()
            
            print('📊 ACCOUNT INFORMATION')
            print('-' * 30)
            print(f'Login Status: Connected')
            print(f'Account Number: {account_info.get("login", "N/A")}')
            print(f'Server: {account_info.get("server", "Exness")}')
            print(f'Account Balance: ${account_info.get("balance", 0):.2f}')
            print(f'Account Equity: ${account_info.get("equity", 0):.2f}')
            print(f'Account Currency: {account_info.get("currency", "USD")}')
            print(f'Leverage: {account_info.get("leverage", "N/A")}x')
            print(f'Margin Used: ${account_info.get("margin", 0):.2f}')
            print(f'Free Margin: ${account_info.get("free_margin", 0):.2f}')
            print(f'Current Profit: ${account_info.get("profit", 0):.2f}')
            print()
            
            # Get positions
            positions = await mt5_integration.get_positions()
            print('📈 CURRENT POSITIONS')
            print('-' * 30)
            if positions:
                for pos in positions:
                    print(f'Symbol: {pos.symbol}')
                    print(f'Type: {"BUY" if pos.type == 0 else "SELL"}')
                    print(f'Volume: {pos.volume} lots')
                    print(f'Entry: ${pos.price_open:.5f}')
                    print(f'Current: ${pos.price_current:.5f}')
                    print(f'Profit: ${pos.profit:.2f}')
                    print('-' * 20)
            else:
                print('No open positions')
            print()
            
            # Get symbol info for key pairs
            print('🎯 SYMBOL STATUS')
            print('-' * 30)
            symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY']
            for symbol in symbols:
                symbol_info = await mt5_integration.get_symbol_info(symbol)
                if symbol_info:
                    print(f'{symbol}: ✅ Available')
                    print(f'  - Spread: {symbol_info.spread} points')
                    print(f'  - Min Lot: {symbol_info.volume_min}')
                    print(f'  - Max Lot: {symbol_info.volume_max}')
                else:
                    print(f'{symbol}: ❌ Not Available')
                print()
            
            print('🎉 CONNECTION STATUS: HEALTHY')
            print('UOTA ELITE v2 is ready to trade!')
            
        else:
            print('❌ MT5 Connection: FAILED')
            print()
            print('🔧 TROUBLESHOOTING:')
            print('1. Check Exness credentials in .env file')
            print('2. Ensure MT5 terminal is running (if using Wine)')
            print('3. Verify network connectivity')
            print('4. Check if Exness server is accessible')
            
        print('=' * 50)
        
    except Exception as e:
        print(f'❌ Error checking connection: {e}')
        # import traceback  # Moved to function to avoid circular import
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_mt5_connection())
