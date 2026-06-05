"""Custom exceptions for MTB-Evo."""


class MTBEvoError(Exception):
    """Base exception for MTB-Evo."""
    pass


class ConfigurationError(MTBEvoError):
    """Configuration-related errors."""
    pass


class ToolNotFoundError(MTBEvoError):
    """Required tool not found."""
    
    def __init__(self, missing_tools: list):
        self.missing_tools = missing_tools
        tools_str = ", ".join(missing_tools)
        super().__init__(
            f"Missing required tools: {tools_str}. "
            "Please activate conda environment: conda activate mtb-evo"
        )


class PipelineError(MTBEvoError):
    """Pipeline execution error."""
    
    def __init__(self, message: str, step: int = None, details: dict = None):
        self.step = step
        self.details = details or {}
        step_info = f" [Step {step}]" if step else ""
        super().__init__(f"{message}{step_info}")


class FileNotFoundError(MTBEvoError):
    """Required file not found."""
    pass


class ValidationError(MTBEvoError):
    """Input validation error."""
    pass
