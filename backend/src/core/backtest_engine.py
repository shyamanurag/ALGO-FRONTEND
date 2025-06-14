# backtesting/backtest_engine.py
"""
Comprehensive Backtesting Framework
Simulates trading strategies on historical data with realistic constraints
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import logging
from collections import defaultdict
import json
from pathlib import Path

import asyncio
from concurrent.futures import ProcessPoolExecutor

from .trade_engine import TradeSignal
from .market_data import MarketDataManager

# Initialize the process pool executor for parallel backtesting
executor = ProcessPoolExecutor()

logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    start_date: datetime
    end_date: datetime

    # Realistic constraints

    # Position limits

    # Order constraints

    # Market hours

    # Data settings

@dataclass
class BacktestOrder:
    """Order representation in backtest"""
    order_id: str
    timestamp: datetime
    symbol: str
    option_type: str  # CE/PE
    strike: float
    side: str  # BUY/SELL
    quantity: int
    order_type: str  # MARKET/LIMIT
    limit_price: Optional[float]

@dataclass
class BacktestPosition:
    """Position tracking in backtest"""
    position_id: str
    symbol: str
    option_type: str
    strike: float
    entry_time: datetime
    entry_price: float
    quantity: int
    current_price: float

@dataclass
class BacktestResults:
    """Comprehensive backtest results"""
    # Overall metrics
    total_return: float
    total_return_percent: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int  # days

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float

    # Time metrics
    average_holding_time: timedelta
    trades_per_day: float

    # Strategy breakdown
    strategy_performance: Dict[str, Dict]

    # Daily metrics
    daily_returns: pd.Series
    equity_curve: pd.Series
    drawdown_series: pd.Series

    # Trade log
    trades: List[BacktestPosition]

    # System metrics
    max_concurrent_positions: int
    order_fill_rate: float
    slippage_cost_total: float
    commission_cost_total: float

@dataclass
class BacktestResult:
    """Results from backtesting"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Dict[str, Any]]
    equity_curve: pd.Series
    daily_returns: pd.Series
    metrics: Dict[str, float]

@dataclass
class WalkForwardResult:
    """Results from walk-forward analysis"""
    in_sample_metrics: Dict[str, float]
    out_of_sample_metrics: Dict[str, float]
    parameter_stability: Dict[str, List[float]]
    performance_decay: float

@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation"""
    confidence_intervals: Dict[str, List[float]]
    worst_case_scenario: Dict[str, float]
    best_case_scenario: Dict[str, float]
    probability_of_profit: float
    expected_max_drawdown: float

class BacktestEngine:
    """
    Main backtesting engine
    Simulates realistic market conditions and constraints
    """

    def __init__(self, 
                 market_data: MarketDataManager,
                 initial_capital: float = 100000.0,
                 commission: float = 0.001,  # 0.1% per trade
                 slippage: float = 0.001):  # 0.1% slippage
        self.market_data = market_data
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.current_capital = initial_capital
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = []
        self.config = BacktestConfig(start_date=datetime.now(), end_date=datetime.now() + timedelta(days=365))
        self._market_data_lock = asyncio.Lock()
        self.historical_data = {}
        self.current_time = None
        self.orders_this_second = 0
        self.last_order_second = None
        self.order_history = []
        self.trade_history = []
        self.performance_metrics = {}
        self.executor = ProcessPoolExecutor()

    async def load_historical_data(self):
        """Load historical data for all symbols"""
        async with self._market_data_lock:
            try:
                for symbol in self.config.symbols:
                    data = await self._load_symbol_data(symbol)
                    if data is not None:
                        self.historical_data[symbol] = data
                        logger.info(f"Loaded historical data for {symbol}")
            except Exception as e:
                logger.error(f"Error loading historical data: {e}")

    async def _get_market_snapshot(self, timestamp: datetime) -> Dict:
        """Get market data snapshot for a specific timestamp"""
        async with self._market_data_lock:
            snapshot = {}
            for symbol in self.config.symbols:
                if symbol in self.historical_data:
                    data = self.historical_data[symbol]
                    # Get the closest timestamp data
                    closest_idx = data.index.get_indexer([timestamp], method='nearest')[0]
                    snapshot[symbol] = {
                        'timestamp': timestamp,
                        'open': data.iloc[closest_idx]['open'],
                        'high': data.iloc[closest_idx]['high'],
                        'low': data.iloc[closest_idx]['low'],
                        'close': data.iloc[closest_idx]['close'],
                        'volume': data.iloc[closest_idx]['volume']
                    }
            return snapshot

    async def _generate_signals(self, strategy_portfolio, market_data: Dict) -> List[Signal]:
        """Generate trading signals from strategies"""
        all_signals = []

        # Evaluate each strategy
        for name, strategy in strategy_portfolio.strategies.items():
            try:
                signals = await strategy.generate_signals(market_data)
                all_signals.extend(signals)
            except Exception as e:
                logger.error(f"Error in strategy {name}: {e}")
                continue

        # Apply confluence detection
        enhanced_signals = await strategy_portfolio.strategies['confluence_amplifier'].analyze_signals(all_signals)
        
        # Filter by quality
        qualified_signals = [s for s in enhanced_signals if s.quality_score >= 8.0]
        
        # Sort by quality and return top 5 signals
        return sorted(qualified_signals, key=lambda x: x.quality_score, reverse=True)[:5]

    def _calculate_position_size(self, signal: Signal) -> int:
        """Calculate position size based on signal and risk management"""
        # Base position size (lots)
        if signal.symbol.startswith('NIFTY'):
            lot_size = 60  # New lot size
            base_lots = 2
        else:  # BANKNIFTY
            lot_size = 40  # New lot size
            base_lots = 1

        # Adjust based on signal quality
        quality_multiplier = signal.quality_score / 10

        # Adjust based on strategy allocation
        allocation = signal.strategy.allocation if hasattr(signal, 'strategy') else 0.2

        # Calculate final size
        position_lots = int(base_lots * quality_multiplier * allocation)
        position_lots = max(1, position_lots)  # Minimum 1 lot

        return position_lots * lot_size

    def _can_place_order(self) -> bool:
        """Check if order can be placed (rate limiting)"""
        current_second = self.current_time.replace(microsecond=0)
        if current_second != self.last_order_second:
            self.orders_this_second = 0
            self.last_order_second = current_second
        return self.orders_this_second < self.config.max_orders_per_second

    def _update_order_tracking(self, order: Order):
        """Update order tracking for rate limiting"""
        current_second = self.current_time.replace(microsecond=0)
        if current_second != self.last_order_second:
            self.orders_this_second = 0
            self.last_order_second = current_second
        self.orders_this_second += 1

    async def run_backtest(self,
                          strategy: Any,
                          symbols: List[str],
                          start_date: datetime,
                          end_date: datetime,
                          timeframe: str = '1d') -> BacktestResult:
        """Run backtest for a strategy"""
        try:
            # Get historical data
            data = await self.market_data.get_historical_data(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe
            )
            
            # Initialize results
            self.current_capital = self.initial_capital
            self.positions = {}
            self.trades = []
            self.equity_curve = [self.initial_capital]
            
            # Run simulation
            for timestamp, bars in self._iterate_data(data):
                # Generate signals
                signals = await strategy.generate_signals(bars)
                
                # Process signals
                for signal in signals:
                    await self._process_signal(signal, bars[signal.symbol])
                    
                # Update equity curve
                self._update_equity_curve(bars)
                
            # Calculate metrics
            metrics = self._calculate_metrics()
            
            return BacktestResult(
                strategy_id=strategy.__class__.__name__,
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                final_capital=self.current_capital,
                total_trades=len(self.trades),
                winning_trades=metrics['winning_trades'],
                losing_trades=metrics['losing_trades'],
                win_rate=metrics['win_rate'],
                profit_factor=metrics['profit_factor'],
                max_drawdown=metrics['max_drawdown'],
                sharpe_ratio=metrics['sharpe_ratio'],
                trades=self.trades,
                equity_curve=pd.Series(self.equity_curve, index=pd.date_range(start_date, end_date)),
                daily_returns=metrics['daily_returns'],
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise
            
    async def _process_signal(self, signal: TradeSignal, bar: pd.Series):
        """Process a trading signal"""
        try:
            # Calculate execution price with slippage
            execution_price = bar['close'] * (1 + self.slippage if signal.direction == 'BUY' else 1 - self.slippage)
            
            # Calculate commission
            commission = execution_price * signal.quantity * self.commission
            
            # Update capital
            if signal.direction == 'BUY':
                cost = execution_price * signal.quantity + commission
                self.current_capital -= cost
            else:
                proceeds = execution_price * signal.quantity - commission
                self.current_capital += proceeds
                
            # Record trade
            trade = {
                'timestamp': bar.name,
                'symbol': signal.symbol,
                'direction': signal.direction,
                'quantity': signal.quantity,
                'entry_price': execution_price,
                'stop_loss': signal.stop_loss,
                'target': signal.target,
                'commission': commission,
                'pnl': 0.0  # Will be updated when position is closed
            }
            self.trades.append(trade)
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            
    def _update_equity_curve(self, bars: Dict[str, pd.Series]):
        """Update equity curve with current positions"""
        try:
            # Calculate position values
            position_value = 0.0
            for symbol, position in self.positions.items():
                price = bars[symbol]['close']
                position_value += price * position['quantity']
                
            # Update equity curve
            equity = self.current_capital + position_value
            self.equity_curve.append(equity)
            
        except Exception as e:
            logger.error(f"Error updating equity curve: {e}")
            
    def _calculate_metrics(self) -> Dict[str, float]:
        """Calculate backtest performance metrics"""
        try:
            # Convert equity curve to returns
            equity_series = pd.Series(self.equity_curve)
            daily_returns = equity_series.pct_change().dropna()
            
            # Calculate basic metrics
            total_return = (self.current_capital - self.initial_capital) / self.initial_capital
            annual_return = (1 + total_return) ** (252 / len(daily_returns)) - 1
            volatility = daily_returns.std() * np.sqrt(252)
            sharpe_ratio = annual_return / volatility if volatility != 0 else 0
            
            # Calculate drawdown
            rolling_max = equity_series.expanding().max()
            drawdowns = equity_series / rolling_max - 1
            max_drawdown = drawdowns.min()
            
            # Calculate trade metrics
            winning_trades = sum(1 for t in self.trades if t['pnl'] > 0)
            losing_trades = sum(1 for t in self.trades if t['pnl'] <= 0)
            win_rate = winning_trades / len(self.trades) if self.trades else 0
            
            # Calculate profit factor
            gross_profit = sum(t['pnl'] for t in self.trades if t['pnl'] > 0)
            gross_loss = abs(sum(t['pnl'] for t in self.trades if t['pnl'] < 0))
            profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
            
            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'daily_returns': daily_returns
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            raise
            
    def _iterate_data(self, data: Dict[str, pd.DataFrame]):
        """Iterate through historical data chronologically"""
        # Get all timestamps
        timestamps = set()
        for df in data.values():
            timestamps.update(df.index)
        timestamps = sorted(list(timestamps))
        
        # Yield data for each timestamp
        for timestamp in timestamps:
            bars = {}
            for symbol, df in data.items():
                if timestamp in df.index:
                    bars[symbol] = df.loc[timestamp]
            yield timestamp, bars
            
    def save_results(self, result: BacktestResult, output_dir: str):
        """Save backtest results to files"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save metrics
            metrics_file = output_path / f"{result.strategy_id}_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump({
                    'strategy_id': result.strategy_id,
                    'start_date': result.start_date.isoformat(),
                    'end_date': result.end_date.isoformat(),
                    'initial_capital': result.initial_capital,
                    'final_capital': result.final_capital,
                    'total_trades': result.total_trades,
                    'winning_trades': result.winning_trades,
                    'losing_trades': result.losing_trades,
                    'win_rate': result.win_rate,
                    'profit_factor': result.profit_factor,
                    'max_drawdown': result.max_drawdown,
                    'sharpe_ratio': result.sharpe_ratio
                }, f, indent=2)
                
            # Save trades
            trades_file = output_path / f"{result.strategy_id}_trades.csv"
            pd.DataFrame(result.trades).to_csv(trades_file, index=False)
            
            # Save equity curve
            equity_file = output_path / f"{result.strategy_id}_equity.csv"
            result.equity_curve.to_csv(equity_file)
            
            logger.info(f"Backtest results saved to {output_dir}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise

    async def _load_symbol_data(self, symbol: str) -> pd.DataFrame:
        """Load historical data for symbol"""
        # Implement based on your data source
        # This is a placeholder
        return pd.DataFrame()

    async def _load_options_data(self, symbol: str) -> Dict:
        """Load historical options chain data"""
        # Implement based on your data source
        return {}

    def _get_options_snapshot(self, symbol: str, timestamp: datetime) -> Dict:
        """Get options chain snapshot at timestamp"""
        # Implement based on your options data structure
        return {}

    def _get_option_price(self, option_key: str, market_data: Dict) -> Optional[float]:
        """Get option price from market data"""
        # Implement based on your data structure
        return None

    def _create_order(self, signal, position_size: int) -> BacktestOrder:
        """Create order from signal"""
        return BacktestOrder(
            order_id=f"BT_{datetime.now().timestamp()}",
            timestamp=self.current_time,
            symbol=signal.symbol,
            option_type=signal.option_type,
            strike=signal.strike,
            side="BUY",  # Always buying options
            quantity=position_size,
            order_type="LIMIT" if hasattr(signal, 'limit_price') else "MARKET",
            limit_price=getattr(signal, 'limit_price', None),
            strategy=signal.strategy_name,
            signal_quality=signal.quality_score
        )

    def _create_position(self, order: BacktestOrder) -> BacktestPosition:
        """Create position from filled order"""
        return BacktestPosition(
            position_id=f"POS_{order.order_id}",
            symbol=order.symbol,
            option_type=order.option_type,
            strike=order.strike,
            entry_time=order.fill_time,
            entry_price=order.executed_price,
            quantity=order.quantity,
            current_price=order.executed_price,
            strategy=order.strategy
        )

    async def run_walk_forward_analysis(self,
                                      strategy: Any,
                                      symbols: List[str],
                                      start_date: datetime,
                                      end_date: datetime,
                                      window_size: int = 252,  # 1 year
                                      step_size: int = 63,    # 3 months
                                      optimization_params: Dict[str, List[Any]] = None) -> WalkForwardResult:
        """Run walk-forward analysis"""
        try:
            # Initialize results
            in_sample_metrics = []
            out_of_sample_metrics = []
            parameter_stability = defaultdict(list)
            
            # Generate time windows
            windows = self._generate_walk_forward_windows(start_date, end_date, window_size, step_size)
            
            for train_start, train_end, test_start, test_end in windows:
                # Optimize on in-sample data
                if optimization_params:
                    best_params = await self._optimize_parameters(
                        strategy, symbols, train_start, train_end, optimization_params
                    )
                    strategy.update_parameters(best_params)
                    
                    # Track parameter stability
                    for param, value in best_params.items():
                        parameter_stability[param].append(value)
                
                # Run in-sample backtest
                in_sample_result = await self.run_backtest(
                    strategy, symbols, train_start, train_end
                )
                in_sample_metrics.append(in_sample_result.metrics)
                
                # Run out-of-sample backtest
                out_of_sample_result = await self.run_backtest(
                    strategy, symbols, test_start, test_end
                )
                out_of_sample_metrics.append(out_of_sample_result.metrics)
            
            # Calculate performance decay
            performance_decay = self._calculate_performance_decay(
                in_sample_metrics, out_of_sample_metrics
            )
            
            return WalkForwardResult(
                in_sample_metrics=self._aggregate_metrics(in_sample_metrics),
                out_of_sample_metrics=self._aggregate_metrics(out_of_sample_metrics),
                parameter_stability=dict(parameter_stability),
                performance_decay=performance_decay
            )
            
        except Exception as e:
            logger.error(f"Walk-forward analysis failed: {e}")
            raise
            
    async def run_monte_carlo_simulation(self,
                                       strategy: Any,
                                       symbols: List[str],
                                       start_date: datetime,
                                       end_date: datetime,
                                       n_simulations: int = 1000) -> MonteCarloResult:
        """Run Monte Carlo simulation"""
        try:
            # Run base backtest
            base_result = await self.run_backtest(strategy, symbols, start_date, end_date)
            
            # Get daily returns
            daily_returns = base_result.daily_returns
            
            # Run simulations
            futures = []
            for _ in range(n_simulations):
                future = self.executor.submit(
                    self._run_single_simulation,
                    daily_returns,
                    self.initial_capital
                )
                futures.append(future)
            
            # Collect results
            simulation_results = []
            for future in futures:
                result = future.result()
                simulation_results.append(result)
            
            # Calculate statistics
            final_values = [r['final_value'] for r in simulation_results]
            max_drawdowns = [r['max_drawdown'] for r in simulation_results]
            
            # Calculate confidence intervals
            confidence_intervals = {
                'final_value': np.percentile(final_values, [5, 25, 50, 75, 95]),
                'max_drawdown': np.percentile(max_drawdowns, [5, 25, 50, 75, 95])
            }
            
            # Calculate probability of profit
            probability_of_profit = sum(1 for v in final_values if v > self.initial_capital) / n_simulations
            
            return MonteCarloResult(
                confidence_intervals=confidence_intervals,
                worst_case_scenario={
                    'final_value': min(final_values),
                    'max_drawdown': max(max_drawdowns)
                },
                best_case_scenario={
                    'final_value': max(final_values),
                    'max_drawdown': min(max_drawdowns)
                },
                probability_of_profit=probability_of_profit,
                expected_max_drawdown=np.mean(max_drawdowns)
            )
            
        except Exception as e:
            logger.error(f"Monte Carlo simulation failed: {e}")
            raise
            
    def _generate_walk_forward_windows(self,
                                     start_date: datetime,
                                     end_date: datetime,
                                     window_size: int,
                                     step_size: int) -> List[Tuple[datetime, datetime, datetime, datetime]]:
        """Generate walk-forward analysis windows"""
        windows = []
        current_start = start_date
        
        while current_start + timedelta(days=window_size) <= end_date:
            train_end = current_start + timedelta(days=window_size)
            test_end = train_end + timedelta(days=step_size)
            
            if test_end > end_date:
                test_end = end_date
                
            windows.append((current_start, train_end, train_end, test_end))
            current_start += timedelta(days=step_size)
            
        return windows
        
    async def _optimize_parameters(self,
                                 strategy: Any,
                                 symbols: List[str],
                                 start_date: datetime,
                                 end_date: datetime,
                                 param_grid: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Optimize strategy parameters"""
        try:
            best_params = None
            best_sharpe = float('-inf')
            
            # Generate parameter combinations
            param_combinations = self._generate_param_combinations(param_grid)
            
            for params in param_combinations:
                # Update strategy parameters
                strategy.update_parameters(params)
                
                # Run backtest
                result = await self.run_backtest(strategy, symbols, start_date, end_date)
                
                # Update best parameters
                if result.metrics['sharpe_ratio'] > best_sharpe:
                    best_sharpe = result.metrics['sharpe_ratio']
                    best_params = params
                    
            return best_params
            
        except Exception as e:
            logger.error(f"Parameter optimization failed: {e}")
            raise
            
    def _generate_param_combinations(self, param_grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Generate parameter combinations for optimization"""
        import itertools
        
        keys = param_grid.keys()
        values = param_grid.values()
        
        combinations = []
        for combination in itertools.product(*values):
            combinations.append(dict(zip(keys, combination)))
            
        return combinations
        
    def _calculate_performance_decay(self,
                                   in_sample_metrics: List[Dict[str, float]],
                                   out_of_sample_metrics: List[Dict[str, float]]) -> float:
        """Calculate performance decay between in-sample and out-of-sample"""
        try:
            in_sample_sharpe = np.mean([m['sharpe_ratio'] for m in in_sample_metrics])
            out_of_sample_sharpe = np.mean([m['sharpe_ratio'] for m in out_of_sample_metrics])
            
            return (in_sample_sharpe - out_of_sample_sharpe) / in_sample_sharpe
            
        except Exception as e:
            logger.error(f"Error calculating performance decay: {e}")
            return float('inf')
            
    def _aggregate_metrics(self, metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
        """Aggregate metrics across multiple periods"""
        try:
            aggregated = {}
            for metric in metrics_list[0].keys():
                values = [m[metric] for m in metrics_list]
                aggregated[metric] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating metrics: {e}")
            return {}
            
    def _run_single_simulation(self, daily_returns: pd.Series, initial_capital: float) -> Dict[str, float]:
        """Run single Monte Carlo simulation"""
        try:
            # Generate random returns
            np.random.seed()
            random_returns = daily_returns.sample(n=len(daily_returns), replace=True)
            
            # Calculate equity curve
            equity_curve = initial_capital * (1 + random_returns).cumprod()
            
            # Calculate metrics
            final_value = equity_curve.iloc[-1]
            max_drawdown = (equity_curve / equity_curve.expanding().max() - 1).min()
            
            return {
                'final_value': final_value,
                'max_drawdown': max_drawdown
            }
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation: {e}")
            return {
                'final_value': initial_capital,
                'max_drawdown': 0.0
            }

class BacktestRunner:
    """Run multiple backtests in parallel"""

    async def run_parameter_sweep(self, base_config: BacktestConfig,
                                parameter_grid: Dict,
                                strategy_portfolio) -> Dict:
        """Run parameter sweep across multiple configurations"""
        configs = self._generate_configs(base_config, parameter_grid)
        futures = []

        for config_name, config in configs.items():
            future = executor.submit(
                self._run_single_backtest,
                config,
                strategy_portfolio
            )
            futures.append((config_name, future))
        results = {}

        for config_name, future in futures:
            try:
                result = future.result(timeout=3600)  # 1 hour timeout
                results[config_name] = result
            except Exception as e:
                logger.error(f"Backtest failed for {config_name}: {e}")

        return results

    def _generate_configs(self, base_config: BacktestConfig, parameter_grid: Dict) -> Dict[str, BacktestConfig]:
        """Generate configuration variations"""
        # Implement parameter grid expansion
        return {"base": base_config}

    def _run_single_backtest(self, config: BacktestConfig, strategy_portfolio) -> BacktestResults:
        """Run single backtest (for multiprocessing)"""
        # Create new event loop for process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        engine = BacktestEngine(config)
        # Run backtest
        loop.run_until_complete(engine.load_historical_data())
        results = loop.run_until_complete(engine.run_backtest(strategy_portfolio))
        loop.close()
        return results

    def _update_positions(self, market_data: Dict):
        """Update open positions with current market data"""
        for position_id, position in self.positions.items():
            if position.symbol in market_data:
                current_price = market_data[position.symbol]['close']
                position.current_price = current_price
                position.pnl = (current_price - position.entry_price) * position.quantity
                position.pnl_percent = (position.pnl / (position.entry_price * position.quantity)) * 100

    def _update_metrics(self, current_date: datetime):
        """Update daily metrics"""
        daily_pnl = sum(p.pnl for p in self.positions.values())
        self.daily_pnl[current_date] = daily_pnl
        self.current_capital += daily_pnl
