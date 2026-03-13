"""Configuration management for MTB-Evo."""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class ReferenceConfig(BaseModel):
    """Reference genome configuration."""

    h37rv: Path = Field(description="Path to H37Rv reference genome")
    ancestor: Path = Field(description="Path to ancestor reference genome")


class PPEFilterConfig(BaseModel):
    """PPE/IS filter configuration."""

    enabled: bool = Field(default=True, description="Enable PPE/IS filtering")
    ppe_list: Path = Field(description="Path to PPE/IS loci list")


class ThresholdConfig(BaseModel):
    """Analysis thresholds."""

    depth: int = Field(default=10, description="Minimum sequencing depth")
    coverage: float = Field(default=0.95, description="Minimum genome coverage")
    min_samples: int = Field(default=5, description="Minimum valid samples for filtering")


class Config(BaseModel):
    """Main configuration class."""

    reference: ReferenceConfig
    ppe_filter: PPEFilterConfig
    samples: List[str]
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """Load configuration from YAML file."""
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
