"""
Recommendations Module for Elite Trading
Contains perfect analyzers and elite trade recommendation engine
"""

from .analyzers import (
    PerfectTechnicalAnalyzer,
    PerfectVolumeAnalyzer,
    PerfectPatternAnalyzer,
    PerfectRegimeAnalyzer,
    PerfectMomentumAnalyzer,
    SmartMoneyAnalyzer
)

from .elite_trade_recommender import (
    EliteTradeRecommendation,
    EliteRecommendationEngine
)

__all__ = [
    'PerfectTechnicalAnalyzer',
    'PerfectVolumeAnalyzer', 
    'PerfectPatternAnalyzer',
    'PerfectRegimeAnalyzer',
    'PerfectMomentumAnalyzer',
    'SmartMoneyAnalyzer',
    'EliteTradeRecommendation',
    'EliteRecommendationEngine'
]