"""
AEGIS Routing Base Interfaces
Pluggable interface for network routing algorithms.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class RoutingAlgorithm(ABC):
    @abstractmethod
    def compute_path(self, topology: Any, source: str, destination: str) -> Optional[List[str]]:
        """Computes optimal path between source and destination nodes."""
        pass

    @abstractmethod
    def compute_all_paths(self, topology: Any) -> Dict[str, Dict[str, List[str]]]:
        """Computes path matrix for all node pairs."""
        pass
