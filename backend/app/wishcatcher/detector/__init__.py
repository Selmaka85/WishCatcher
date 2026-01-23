"""
WishCatcher Detectors - Module pentru detectare proactivă și implicită
"""

from .proactive_wish_detector import ProactiveWishDetector
from .implicit_intent_detector import ImplicitIntentDetector
from .conversational_analyzer import ConversationalAnalyzer
from .workaround_detector import WorkaroundDetector
from .comparison_analyzer import ComparisonAnalyzer

__all__ = [
    "ProactiveWishDetector",
    "ImplicitIntentDetector",
    "ConversationalAnalyzer",
    "WorkaroundDetector",
    "ComparisonAnalyzer"
]
