"""Hardware module for BlockSnap camera system."""
from .mock_camera import MockCamera

try:
    from .camera import BlockSnapCamera
except (ImportError, RuntimeError):
    BlockSnapCamera = None

__all__ = ['MockCamera', 'BlockSnapCamera']
