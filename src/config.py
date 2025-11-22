"""
Configuration management for loading and accessing params.yaml.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Manages configuration loaded from params.yaml."""
    
    def __init__(self, params_path: str = "params.yaml"):
        """Load configuration from params.yaml file.
        
        Args:
            params_path: Path to params.yaml file
        """
        self.params_path = Path(params_path)
        if not self.params_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {params_path}")
        
        with open(self.params_path, 'r') as f:
            self._params = yaml.safe_load(f)
    
    @property
    def data(self) -> Dict[str, Any]:
        """Data configuration parameters."""
        return self._params.get('data', {})
    
    @property
    def training(self) -> Dict[str, Any]:
        """Training configuration parameters."""
        return self._params.get('training', {})
    
    @property
    def evaluation(self) -> Dict[str, Any]:
        """Evaluation configuration parameters."""
        return self._params.get('evaluation', {})
    
    @property
    def release(self) -> Dict[str, Any]:
        """Release configuration parameters."""
        return self._params.get('release', {})
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'training.lr')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._params
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def compute_input_dim(self) -> int:
        """Compute input dimension from data config.
        
        Returns:
            Computed input dimension (image_size[0] * image_size[1] * num_channels)
        """
        image_size = self.data.get('image_size', (28, 28))
        num_channels = self.data.get('num_channels', 1)
        if isinstance(image_size, (list, tuple)) and len(image_size) >= 2:
            return image_size[0] * image_size[1] * num_channels
        return 784 * num_channels  # Default 28x28x1

