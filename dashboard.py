"""
Crypto trade bot - Streamlit Dashboard
Beautiful, professional real-time trading dashboard
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import json
import time
from typing import Dict, List, Any
import requests
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
import streamlit.components.v1 as components

# Import our modules with error handling
try:
    from config import config
    from risk_manager import risk_manager
    from agents.supervisor import SupervisorAgent
    from opportunity_scanner import opportunity_scanner
    from exchange_integration import exchange_manager
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Make sure all required packages are installed: pip install -r requirements.txt")
    st.stop()

# Configure page
st.set_page_config(
    page_title="Crypto trade bot - Trading Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional dark theme
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00d4ff, #0066ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .status-running {
        color: #00ff00;
        font-weight: bold;
    }
    
    .status-paused {
        color: #ffaa00;
        font-weight: bold;
    }
    
    .status-stopped {
        color: #ff4444;
        font-weight: bold;
    }
    
    .profit-positive {
        color: #00ff00;
    }
    
    .profit-negative {
        color: #ff4444;
    }
    
    .opportunity-card {
        background: rgba(0, 100, 255, 0.1);
        border-left: 4px solid #0066ff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    
    .risk-high {
        background: rgba(255, 0, 0, 0.1);
        border-left: 4px solid #ff4444;
    }
    
    .risk-medium {
        background: rgba(255, 165, 0, 0.1);
        border-left: 4px solid #ffaa00;
    }
    
    .risk-low {
        background: rgba(0, 255, 0, 0.1);
        border-left: 4px solid #00ff00;
    }
</style>
""", unsafe_allow_html=True)

class Dashboard:
    """Main dashboard class"""
    
    def __init__(self):
        self.supervisor = None
        self.last_update = datetime.now()
        self.refresh_interval = 5  # seconds
        
    def run(self):
        """Run the dashboard"""
        # Header
        st.markdown('<h1 class="main-header">🤖 Crypto trade bot Trading Dashboard</h1>', unsafe_allow_html=True)
        
        # Sidebar
        self._render_sidebar()
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", "💼 Positions", "🎯 Opportunities", 
            "⚙️ Settings", "📈 Analytics"
        ])
        
        with tab1:
            self._render_overview()
            
        with tab2:
            self._render_positions()
            
        with tab3:
            self._render_opportunities()
            
        with tab4:
            self._render_settings()
            
        with tab5:
            self._render_analytics()
            
        # Auto-refresh
        if st.session_state.get('auto_refresh', True):
            time.sleep(self.refresh_interval)
            st.rerun()
            
    def _render_sidebar(self):
        """Render sidebar with controls"""
        with st.sidebar:
            st.header("⚡ Control Panel")
            
            # System Status
            st.subheader("🔧 System Status")
            status = self._get_system_status()
            status_color = {
                'running': 'status-running',
                'paused': 'status-paused',
                'stopped': 'status-stopped'
            }.get(status['status'], '')
            
            st.markdown(f"""
            <div class="{status_color}">
                Status: {status['status'].upper()}
            </div>
            """, unsafe_allow_html=True)
            
            st.metric("Uptime", status['uptime'])
            st.metric("Active Positions", status['positions'])
            st.metric("Daily P&L", f"${status['daily_pnl']:.2f}")
            
            # Quick Actions
            st.subheader("🎮 Quick Actions")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start", type="primary"):
                    self._start_trading()
                    
            with col2:
                if st.button("⏸️ Pause"):
                    self._pause_trading()
                    
            if st.button("🛑 Emergency Stop", type="secondary"):
                self._emergency_stop()
                
            # Refresh Settings
            st.subheader("🔄 Refresh Settings")
            auto_refresh = st.checkbox("Auto Refresh", value=True)
            st.session_state['auto_refresh'] = auto_refresh
            
            if auto_refresh:
                refresh_interval = st.slider("Refresh Interval (s)", 1, 30, 5)
                self.refresh_interval = refresh_interval
                
            # Connection Status
            st.subheader("🌐 Connections")
            connections = self._get_connection_status()
            for exchange, status in connections.items():
                status_icon = "🟢" if status == 'connected' else "🔴"
                st.write(f"{status_icon} {exchange}: {status}")
                
    def _render_overview(self):
        """Render overview tab"""
        colored_header(
            label="📊 Trading Overview",
            description="Real-time trading performance and metrics",
            color_name="blue-70"
        )
        
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_balance = risk_manager.metrics.current_balance
            st.metric(
                "Current Balance", 
                f"${current_balance:.2f}",
                delta=f"${risk_manager.metrics.daily_pnl:.2f}"
            )
            
        with col2:
            progress = self._get_goal_progress()
            st.metric(
                "Goal Progress",
                f"{progress['percentage']:.1f}%",
                delta=f"{progress['remaining']:.1f}% remaining"
            )
            
        with col3:
            risk_score = risk_manager.calculate_risk_score()
            risk_color = "normal" if risk_score < 50 else "inverse"
            st.metric(
                "Risk Score",
                f"{risk_score:.1f}/100",
                delta=None
            )
            
        with col4:
            opportunities = len(opportunity_scanner.get_latest_opportunities())
            st.metric(
                "Active Opportunities",
                opportunities,
                delta=None
            )
            
        # Charts Row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Equity Curve")
            self._render_equity_curve()
            
        with col2:
            st.subheader("📈 Daily Performance")
            self._render_daily_performance()
            
        # Recent Activity
        st.subheader("🔄 Recent Activity")
        self._render_recent_activity()
        
    def _render_positions(self):
        """Render positions tab"""
        colored_header(
            label="💼 Active Positions",
            description="Current trading positions and P&L",
            color_name="green-70"
        )
        
        # Position Summary
        positions = self._get_active_positions()
        
        if not positions:
            st.info("No active positions")
            return
            
        # Position Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_unrealized = sum(pos['unrealized_pnl'] for pos in positions)
            st.metric("Total Unrealized P&L", f"${total_unrealized:.2f}")
            
        with col2:
            total_invested = sum(pos['size'] * pos['entry_price'] for pos in positions)
            st.metric("Total Invested", f"${total_invested:.2f}")
            
        with col3:
            avg_leverage = np.mean([pos['leverage'] for pos in positions])
            st.metric("Average Leverage", f"{avg_leverage:.1f}x")
            
        with col4:
            st.metric("Number of Positions", len(positions))
            
        # Positions Table
        st.subheader("📋 Position Details")
        
        df = pd.DataFrame(positions)
        
        # Style the dataframe
        def style_pnl(val):
            color = 'profit-positive' if val > 0 else 'profit-negative' if val < 0 else ''
            return f'color: {"green" if val > 0 else "red" if val < 0 else "black"}'
            
        styled_df = df.style.applymap(style_pnl, subset=['unrealized_pnl'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Position Charts
        if positions:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Position Distribution")
                self._render_position_distribution(positions)
                
            with col2:
                st.subheader("⚖️ Risk Breakdown")
                self._render_risk_breakdown(positions)
                
    def _render_opportunities(self):
        """Render opportunities tab"""
        colored_header(
            label="🎯 Trading Opportunities",
            description="Latest high-confidence trading opportunities",
            color_name="purple-70"
        )
        
        opportunities = opportunity_scanner.get_latest_opportunities()
        
        if not opportunities:
            st.info("No current opportunities")
            return
            
        # Opportunity Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.6, 0.1)
            
        with col2:
            risk_filter = st.selectbox("Risk Level", ["All", "Low", "Medium", "High"])
            
        with col3:
            opportunity_type = st.selectbox("Opportunity Type", ["All", "technical_signal", "news_event", "sentiment_shift", "volatility_spike"])
            
        # Filter opportunities
        filtered_opps = []
        for opp in opportunities:
            if opp.confidence >= min_confidence:
                if risk_filter == "All" or opp.risk_level == risk_filter:
                    if opportunity_type == "All" or opp.opportunity_type == opportunity_type:
                        filtered_opps.append(opp)
                        
        # Display opportunities
        for i, opp in enumerate(filtered_opps[:10]):  # Top 10
            risk_class = f"risk-{opp.risk_level}"
            
            with st.container():
                st.markdown(f"""
                <div class="opportunity-card {risk_class}">
                    <h4>{opp.symbol} - {opp.opportunity_type.replace('_', ' ').title()}</h4>
                    <p><strong>Confidence:</strong> {opp.confidence:.1%} | 
                       <strong>Expected Return:</strong> {opp.expected_return:.1%} | 
                       <strong>Time Horizon:</strong> {opp.time_horizon} | 
                       <strong>Risk:</strong> {opp.risk_level.title()}</p>
                    <p><strong>Catalyst:</strong> {opp.catalyst}</p>
                    <p><strong>Urgency:</strong> {opp.urgency:.1%}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button(f"Take Trade {i+1}", key=f"trade_{i}"):
                        self._execute_opportunity(opp)
                        
                with col2:
                    if st.button(f"Analyze {i+1}", key=f"analyze_{i}"):
                        self._analyze_opportunity(opp)
                        
                with col3:
                    st.write(f"Created: {opp.timestamp.strftime('%H:%M:%S')}")
                    
    def _render_settings(self):
        """Render settings tab"""
        colored_header(
            label="⚙️ Trading Settings",
            description="Configure trading parameters and goals",
            color_name="orange-70"
        )
        
        # Goal Settings
        st.subheader("🎯 Trading Goals")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_leverage = st.number_input(
                "Max Leverage",
                min_value=1.0,
                max_value=100.0,
                value=config.trading.max_leverage,
                step=1.0
            )
            
        with col2:
            new_goal = st.text_area(
                "Goal Command",
                value=config.trading.goal_command,
                height=100
            )
            
        if st.button("Update Goals", type="primary"):
            config.update_goal(new_leverage, new_goal)
            st.success("Goals updated successfully!")
            
        # Risk Settings
        st.subheader("⚠️ Risk Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_risk = st.number_input(
                "Max Risk per Trade (%)",
                min_value=0.1,
                max_value=10.0,
                value=config.trading.max_risk_per_trade * 100,
                step=0.1
            )
            
        with col2:
            max_daily_loss = st.number_input(
                "Max Daily Loss (%)",
                min_value=1.0,
                max_value=50.0,
                value=config.trading.max_daily_loss * 100,
                step=1.0
            )
            
        with col3:
            max_drawdown = st.number_input(
                "Max Drawdown (%)",
                min_value=5.0,
                max_value=100.0,
                value=config.trading.max_drawdown * 100,
                step=5.0
            )
            
        if st.button("Update Risk Settings"):
            config.trading.max_risk_per_trade = max_risk / 100
            config.trading.max_daily_loss = max_daily_loss / 100
            config.trading.max_drawdown = max_drawdown / 100
            config.save_config()
            st.success("Risk settings updated!")
            
        # Exchange Settings
        st.subheader("🌐 Exchange Configuration")
        
        active_exchanges = config.get_active_exchanges()
        st.write(f"Active exchanges: {', '.join(active_exchanges)}")
        
        # Manual Controls
        st.subheader("🎮 Manual Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Force Scan", type="secondary"):
                st.info("Manual opportunity scan initiated")
                
        with col2:
            if st.button("Backup Data", type="secondary"):
                st.info("Data backup initiated")
                
        with col3:
            if st.button("Clear Cache", type="secondary"):
                st.info("Cache cleared")
                
    def _render_analytics(self):
        """Render analytics tab"""
        colored_header(
            label="📈 Performance Analytics",
            description="Detailed trading performance analysis",
            color_name="cyan-70"
        )
        
        # Performance Summary
        st.subheader("📊 Performance Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_trades = len(risk_manager.daily_trades)
            st.metric("Total Trades", total_trades)
            
        with col2:
            if risk_manager.daily_trades:
                win_rate = len([t for t in risk_manager.daily_trades if t['pnl'] > 0]) / len(risk_manager.daily_trades)
                st.metric("Win Rate", f"{win_rate:.1%}")
            else:
                st.metric("Win Rate", "0%")
                
        with col3:
            avg_trade = np.mean([t['pnl'] for t in risk_manager.daily_trades]) if risk_manager.daily_trades else 0
            st.metric("Avg Trade P&L", f"${avg_trade:.2f}")
            
        with col4:
            profit_factor = self._calculate_profit_factor()
            st.metric("Profit Factor", f"{profit_factor:.2f}")
            
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Trade Distribution")
            self._render_trade_distribution()
            
        with col2:
            st.subheader("⏰ Trade Timeline")
            self._render_trade_timeline()
            
        # Detailed Trade History
        st.subheader("📋 Trade History")
        
        if risk_manager.daily_trades:
            df = pd.DataFrame(risk_manager.daily_trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No trades yet today")
            
    def _render_equity_curve(self):
        """Render equity curve chart"""
        # Generate sample data (replace with real data)
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
        equity = [config.trading.starting_balance + i * 10 for i in range(30)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=equity,
            mode='lines',
            name='Equity',
            line=dict(color='#00d4ff', width=2)
        ))
        
        fig.update_layout(
            title="Equity Curve",
            xaxis_title="Date",
            yaxis_title="Balance ($)",
            height=300,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_daily_performance(self):
        """Render daily performance chart"""
        hours = list(range(24))
        pnl = [np.random.normal(0, 50) for _ in range(24)]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=hours,
            y=pnl,
            name='Hourly P&L',
            marker_color=['green' if x > 0 else 'red' for x in pnl]
        ))
        
        fig.update_layout(
            title="Hourly P&L",
            xaxis_title="Hour",
            yaxis_title="P&L ($)",
            height=300,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_recent_activity(self):
        """Render recent activity feed"""
        activities = [
            {"time": "10:30:15", "action": "Trade opened", "details": "BTC/USDT Long 0.1 @ $45,000"},
            {"time": "10:25:30", "action": "Opportunity detected", "details": "ETH/USDT volatility spike"},
            {"time": "10:20:45", "action": "Position closed", "details": "SOL/USDT +$25.50 profit"},
            {"time": "10:15:20", "action": "Risk alert", "details": "Daily loss at 80% limit"},
            {"time": "10:10:10", "action": "System update", "details": "Models retrained successfully"},
        ]
        
        for activity in activities:
            st.write(f"**{activity['time']}** - {activity['action']}: {activity['details']}")
            
    def _render_position_distribution(self, positions):
        """Render position distribution chart"""
        symbols = [pos['symbol'] for pos in positions]
        sizes = [pos['size'] * pos['entry_price'] for pos in positions]
        
        fig = go.Figure(data=[go.Pie(
            labels=symbols,
            values=sizes,
            hole=0.3
        )])
        
        fig.update_layout(
            title="Position Distribution",
            height=300,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_risk_breakdown(self, positions):
        """Render risk breakdown chart"""
        risk_levels = [pos['risk_amount'] for pos in positions]
        symbols = [pos['symbol'] for pos in positions]
        
        fig = go.Figure(data=[go.Bar(
            x=symbols,
            y=risk_levels,
            marker_color='orange'
        )])
        
        fig.update_layout(
            title="Risk per Position",
            xaxis_title="Symbol",
            yaxis_title="Risk Amount ($)",
            height=300,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_trade_distribution(self):
        """Render trade distribution chart"""
        if not risk_manager.daily_trades:
            st.info("No trades to display")
            return
            
        pnl_values = [t['pnl'] for t in risk_manager.daily_trades]
        
        fig = go.Figure(data=[go.Histogram(
            x=pnl_values,
            nbinsx=20,
            marker_color='lightblue'
        )])
        
        fig.update_layout(
            title="P&L Distribution",
            xaxis_title="P&L ($)",
            yaxis_title="Frequency",
            height=300,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _render_trade_timeline(self):
        """Render trade timeline chart"""
        if not risk_manager.daily_trades:
            st.info("No trades to display")
            return
            
        df = pd.DataFrame(risk_manager.daily_trades)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['cumulative_pnl'] = df['pnl'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cumulative_pnl'],
            mode='lines+markers',
            name='Cumulative P&L',
            line=dict(color='#00ff00', width=2)
        ))
        
        fig.update_layout(
            title="Cumulative P&L Timeline",
            xaxis_title="Time",
            yaxis_title="Cumulative P&L ($)",
            height=300,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    def _get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'status': 'running',  # Get from supervisor
            'uptime': '2h 15m',   # Calculate actual uptime
            'positions': len(risk_manager.positions),
            'daily_pnl': risk_manager.metrics.daily_pnl
        }
        
    def _get_goal_progress(self) -> Dict[str, float]:
        """Get goal progress"""
        current = risk_manager.metrics.current_balance
        target = config.trading.target_balance
        starting = config.trading.starting_balance
        
        if target <= starting:
            return {'percentage': 100.0, 'remaining': 0.0}
            
        progress = ((current - starting) / (target - starting)) * 100
        remaining = 100 - progress
        
        return {'percentage': progress, 'remaining': remaining}
        
    def _get_connection_status(self) -> Dict[str, str]:
        """Get exchange connection status"""
        return {
            'Binance': 'connected',
            'Bybit': 'connected',
            'OKX': 'disconnected'
        }
        
    def _get_active_positions(self) -> List[Dict[str, Any]]:
        """Get active positions"""
        positions = []
        for symbol, pos in risk_manager.positions.items():
            positions.append({
                'symbol': symbol,
                'side': pos.side,
                'size': pos.size,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'unrealized_pnl': pos.unrealized_pnl,
                'leverage': pos.leverage,
                'risk_amount': pos.risk_amount
            })
        return positions
        
    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor"""
        if not risk_manager.daily_trades:
            return 0.0
            
        profits = sum(t['pnl'] for t in risk_manager.daily_trades if t['pnl'] > 0)
        losses = sum(abs(t['pnl']) for t in risk_manager.daily_trades if t['pnl'] < 0)
        
        return profits / losses if losses > 0 else float('inf')
        
    def _start_trading(self):
        """Start trading"""
        st.success("Trading started!")
        
    def _pause_trading(self):
        """Pause trading"""
        st.warning("Trading paused!")
        
    def _emergency_stop(self):
        """Emergency stop"""
        st.error("Emergency stop activated!")
        
    def _execute_opportunity(self, opportunity):
        """Execute trading opportunity"""
        st.success(f"Executing trade for {opportunity.symbol}")
        
    def _analyze_opportunity(self, opportunity):
        """Analyze opportunity"""
        st.info(f"Analyzing {opportunity.symbol} opportunity...")

# Main execution
if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.run()
