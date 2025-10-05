"""AI Token Manager + Exo Bridge - Core Package"""

__version__ = "0.1.0"
__author__ = "AI Token Manager + Exo Bridge Contributors"
__description__ = "Clean adapter bridging ai-token-manager with Exo distributed AI"

from .exo_provider import ExoClusterProvider
from .exo_integration import ExoTokenManagerIntegration, ExoReliakitProvider

__all__ = [
    "ExoClusterProvider",
    "ExoTokenManagerIntegration",
    "ExoReliakitProvider",
]
