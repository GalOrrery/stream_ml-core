"""Utilities."""

from stream_ml.core.utils.compat import array_at, get_namespace
from stream_ml.core.utils.funcs import within_bounds
from stream_ml.core.utils.scale._api import DataScaler
from stream_ml.core.utils.scale._multi import CompoundDataScaler
from stream_ml.core.utils.scale._standard import StandardScaler

__all__ = [
    "array_at",
    "get_namespace",
    "within_bounds",
    "DataScaler",
    "CompoundDataScaler",
    "StandardScaler",
]
