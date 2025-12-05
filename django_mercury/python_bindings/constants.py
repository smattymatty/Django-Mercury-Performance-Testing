"""Performance Testing Framework Constants and Configuration

This module centralizes all magic numbers, thresholds, and configuration
constants used throughout the performance testing framework.
"""

from typing import Dict, Final, List

# Response time thresholds (in milliseconds)
RESPONSE_TIME_THRESHOLDS: Final[Dict[str, float]] = {
    "EXCELLENT": 50.0,
    "GOOD": 100.0,
    "ACCEPTABLE": 300.0,
    "SLOW": 500.0,
    "CRITICAL": 1000.0,
}

# Memory usage thresholds (in megabytes)
MEMORY_THRESHOLDS: Final[Dict[str, float]] = {
    "EXCELLENT": 20.0,
    "GOOD": 50.0,
    "ACCEPTABLE": 100.0,
    "HIGH": 200.0,
    "CRITICAL": 500.0,
}

# Query count thresholds for different operations
QUERY_COUNT_THRESHOLDS: Final[Dict[str, Dict[str, int]]] = {
    "list_view": {"EXCELLENT": 3, "GOOD": 6, "ACCEPTABLE": 10, "HIGH": 20, "CRITICAL": 50},
    "detail_view": {"EXCELLENT": 2, "GOOD": 4, "ACCEPTABLE": 8, "HIGH": 15, "CRITICAL": 30},
    "create_view": {"EXCELLENT": 3, "GOOD": 6, "ACCEPTABLE": 12, "HIGH": 20, "CRITICAL": 40},
    "update_view": {"EXCELLENT": 3, "GOOD": 5, "ACCEPTABLE": 10, "HIGH": 18, "CRITICAL": 35},
    "delete_view": {"EXCELLENT": 5, "GOOD": 10, "ACCEPTABLE": 20, "HIGH": 35, "CRITICAL": 60},
    "search_view": {"EXCELLENT": 2, "GOOD": 5, "ACCEPTABLE": 12, "HIGH": 25, "CRITICAL": 50},
}

# N+1 detection thresholds
N_PLUS_ONE_THRESHOLDS: Final[Dict[str, int]] = {
    "MINIMUM_FOR_DETECTION": 12,  # Minimum queries to flag as N+1
    "MILD": 12,
    "MODERATE": 18,
    "HIGH": 25,
    "SEVERE": 35,
    "CRITICAL": 50,
}

# Cache performance thresholds
CACHE_HIT_RATIO_THRESHOLDS: Final[Dict[str, float]] = {
    "EXCELLENT": 0.9,
    "GOOD": 0.7,
    "ACCEPTABLE": 0.5,
    "POOR": 0.3,
    "CRITICAL": 0.1,
}

# Django baseline memory usage (in MB)
DJANGO_BASELINE_MEMORY_MB: Final[float] = 80.0

# Performance scoring weights (must sum to 100)
SCORING_WEIGHTS: Final[Dict[str, float]] = {
    "response_time": 30.0,
    "query_efficiency": 40.0,
    "memory_efficiency": 20.0,
    "cache_performance": 10.0,
}

# Performance scoring penalties
SCORING_PENALTIES: Final[Dict[str, float]] = {
    "n_plus_one_mild": 5.0,
    "n_plus_one_moderate": 10.0,
    "n_plus_one_high": 20.0,
    "n_plus_one_severe": 30.0,
    "n_plus_one_critical": 40.0,
}

# Operation type detection keywords
OPERATION_KEYWORDS: Final[Dict[str, List[str]]] = {
    "delete_view": ["delete", "destroy", "remove"],
    "list_view": ["list", "get_all", "index"],
    "detail_view": ["detail", "retrieve", "get_single"],
    "create_view": ["create", "post", "add"],
    "update_view": ["update", "put", "patch", "edit"],
    "search_view": ["search", "filter", "query"],
}

# Environment variable names
ENV_VARS: Final[Dict[str, str]] = {
    "MERCURY_CONFIG_PATH": "MERCURY_CONFIG_PATH",
    "MERCURY_LOG_LEVEL": "MERCURY_LOG_LEVEL",
    "FORCE_COLOR": "FORCE_COLOR",
    "NO_COLOR": "NO_COLOR",
    "CLICOLOR": "CLICOLOR",
    "CLICOLOR_FORCE": "CLICOLOR_FORCE",
}

# Default paths
DEFAULT_PATHS: Final[Dict[str, str]] = {
    "C_LIBRARY": "c_core/libperformance.so",
}

# Maximum values for safety checks
MAX_VALUES: Final[Dict[str, int]] = {
    "RESPONSE_TIME_MS": 60000,  # 1 minute
    "MEMORY_MB": 2048,  # 2 GB
    "QUERY_COUNT": 10000,
    "OPERATION_NAME_LENGTH": 256,
    "ACTIVE_MONITORS": 2048,
}

DEFAULT_THRESHOLDS: Final[Dict[str, Dict[str, float]]] = {
    "response_time": {
        "fast": 100,        
        "normal": 500,      
        "slow": 1000,      
        "critical": 3000,  
    },
    "queries": {
        "efficient": 5,     
        "normal": 20,       
        "excessive": 50,   
    },
    "memory_mb": {
        "efficient": 10,    
        "normal": 50,      
        "high": 100,       
    },
    "cache_hit_ratio": {
        "excellent": 0.9,  
        "good": 0.7,        
        "poor": 0.5,        
    },
}


