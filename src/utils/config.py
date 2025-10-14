"""
Configuration management for the Tableau Dashboard Generator.
Handles loading and validation of application configuration from various sources.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI configuration"""
    endpoint: str
    api_key: str
    api_version: str
    deployment_name: str
    model_name: str
    temperature: float = 0.3
    max_tokens: int = 4000
    top_p: float = 0.9

@dataclass  
class ApplicationConfig:
    """Application-level configuration"""
    name: str = "Tableau Dashboard Generator"
    version: str = "1.0.0"
    description: str = "AI-powered automatic Tableau dashboard generation"
    debug: bool = False
    log_level: str = "INFO"

@dataclass
class FileStorageConfig:
    """File storage configuration"""
    upload_folder: str = "./data/uploads"
    output_folder: str = "./data/outputs"
    temp_folder: str = "./data/temp"
    max_file_size_mb: int = 100

@dataclass
class DashboardGenerationConfig:
    """Dashboard generation configuration"""
    max_worksheets_per_workbook: int = 10
    max_dashboards_per_workbook: int = 5
    default_width: int = 1200
    default_height: int = 800
    visualization_types: Dict[str, List[str]] = None
    color_schemes: Dict[str, Any] = None

@dataclass
class DataProcessingConfig:
    """Data processing configuration"""
    max_file_size_mb: int = 100
    supported_formats: List[str] = None
    auto_detect_types: bool = True
    sample_rows_for_analysis: int = 1000
    null_threshold: float = 0.3

@dataclass
class MetaPromptingConfig:
    """Meta-prompting configuration"""
    system_prompts: Dict[str, str] = None

@dataclass
class StreamlitConfig:
    """Streamlit configuration"""
    server_port: int = 8501
    server_address: str = "localhost"
    page_config: Dict[str, Any] = None

class Config:
    """
    Main configuration class that loads and manages all application settings.
    """
    
    def __init__(self, config_file: Optional[str] = None, env_file: Optional[str] = None):
        """
        Initialize configuration from file and environment variables.
        
        Args:
            config_file: Path to YAML configuration file
            env_file: Path to .env file
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()  # Load from default .env file if exists
        
        # Load configuration file
        self.config_data = self._load_config_file(config_file or "config.yaml")
        
        # Initialize configuration sections
        self.azure_openai = self._init_azure_openai_config()
        self.application = self._init_application_config()
        self.file_storage = self._init_file_storage_config()
        self.dashboard_generation = self._init_dashboard_generation_config()
        self.data_processing = self._init_data_processing_config()
        self.meta_prompting = self._init_meta_prompting_config()
        self.streamlit = self._init_streamlit_config()
        
        # Validate configuration
        self._validate_config()
    
    def _load_config_file(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            # Create default config if it doesn't exist
            return self._create_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load config file {config_file}: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
            "application": {
                "name": "Tableau Dashboard Generator",
                "version": "1.0.0",
                "description": "AI-powered automatic Tableau dashboard generation"
            },
            "azure_openai": {
                "api_version": "2024-02-15-preview",
                "max_tokens": 4000,
                "temperature": 0.3,
                "top_p": 0.9
            },
            "dashboard_generation": {
                "max_worksheets_per_workbook": 10,
                "max_dashboards_per_workbook": 5,
                "default_dimensions": {"width": 1200, "height": 800},
                "visualization_types": {
                    "numeric": ["bar", "line", "area", "scatter", "histogram"],
                    "categorical": ["bar", "pie", "treemap", "packed_bubbles"],
                    "geographic": ["map", "filled_map"],
                    "temporal": ["line", "area", "gantt"]
                },
                "color_schemes": {
                    "default": "tableau10",
                    "categorical": ["tableau10", "tableau20", "category10"],
                    "sequential": ["blues", "oranges", "greens"],
                    "diverging": ["red_blue", "orange_blue", "green_orange"]
                }
            },
            "data_processing": {
                "max_file_size_mb": 100,
                "supported_formats": ["csv", "xlsx", "json", "parquet"],
                "auto_detect_types": True,
                "sample_rows_for_analysis": 1000,
                "null_threshold": 0.3
            },
            "meta_prompting": {
                "system_prompts": {
                    "data_analyzer": "You are an expert data analyst specializing in business intelligence and Tableau dashboard design.",
                    "dashboard_designer": "You are a professional Tableau dashboard designer with expertise in creating compelling dashboards.",
                    "worksheet_creator": "You are a Tableau worksheet specialist."
                }
            },
            "streamlit": {
                "page_config": {
                    "page_title": "Tableau Dashboard Generator",
                    "page_icon": "📊",
                    "layout": "wide",
                    "initial_sidebar_state": "expanded"
                }
            }
        }
    
    def _init_azure_openai_config(self) -> AzureOpenAIConfig:
        """Initialize Azure OpenAI configuration"""
        config = self.config_data.get("azure_openai", {})
        
        return AzureOpenAIConfig(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", config.get("api_version", "2024-02-15-preview")),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", ""),
            model_name=os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4-turbo"),
            temperature=float(os.getenv("AZURE_OPENAI_TEMPERATURE", config.get("temperature", 0.3))),
            max_tokens=int(os.getenv("AZURE_OPENAI_MAX_TOKENS", config.get("max_tokens", 4000))),
            top_p=float(os.getenv("AZURE_OPENAI_TOP_P", config.get("top_p", 0.9)))
        )
    
    def _init_application_config(self) -> ApplicationConfig:
        """Initialize application configuration"""
        config = self.config_data.get("application", {})
        
        return ApplicationConfig(
            name=os.getenv("APP_NAME", config.get("name", "Tableau Dashboard Generator")),
            version=os.getenv("APP_VERSION", config.get("version", "1.0.0")),
            description=config.get("description", "AI-powered automatic Tableau dashboard generation"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
    
    def _init_file_storage_config(self) -> FileStorageConfig:
        """Initialize file storage configuration"""
        return FileStorageConfig(
            upload_folder=os.getenv("UPLOAD_FOLDER", "./data/uploads"),
            output_folder=os.getenv("OUTPUT_FOLDER", "./data/outputs"),
            temp_folder=os.getenv("TEMP_FOLDER", "./data/temp"),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "100"))
        )
    
    def _init_dashboard_generation_config(self) -> DashboardGenerationConfig:
        """Initialize dashboard generation configuration"""
        config = self.config_data.get("dashboard_generation", {})
        
        return DashboardGenerationConfig(
            max_worksheets_per_workbook=config.get("max_worksheets_per_workbook", 10),
            max_dashboards_per_workbook=config.get("max_dashboards_per_workbook", 5),
            default_width=config.get("default_dimensions", {}).get("width", 1200),
            default_height=config.get("default_dimensions", {}).get("height", 800),
            visualization_types=config.get("visualization_types", {}),
            color_schemes=config.get("color_schemes", {})
        )
    
    def _init_data_processing_config(self) -> DataProcessingConfig:
        """Initialize data processing configuration"""
        config = self.config_data.get("data_processing", {})
        
        return DataProcessingConfig(
            max_file_size_mb=config.get("max_file_size_mb", 100),
            supported_formats=config.get("supported_formats", ["csv", "xlsx", "json", "parquet"]),
            auto_detect_types=config.get("auto_detect_types", True),
            sample_rows_for_analysis=config.get("sample_rows_for_analysis", 1000),
            null_threshold=config.get("null_threshold", 0.3)
        )
    
    def _init_meta_prompting_config(self) -> MetaPromptingConfig:
        """Initialize meta-prompting configuration"""
        config = self.config_data.get("meta_prompting", {})
        
        return MetaPromptingConfig(
            system_prompts=config.get("system_prompts", {})
        )
    
    def _init_streamlit_config(self) -> StreamlitConfig:
        """Initialize Streamlit configuration"""
        config = self.config_data.get("streamlit", {})
        
        return StreamlitConfig(
            server_port=int(os.getenv("STREAMLIT_SERVER_PORT", "8501")),
            server_address=os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost"),
            page_config=config.get("page_config", {})
        )
    
    def _validate_config(self):
        """Validate configuration settings"""
        errors = []
        
        # Validate Azure OpenAI configuration
        if not self.azure_openai.endpoint:
            errors.append("Azure OpenAI endpoint is required")
        if not self.azure_openai.api_key:
            errors.append("Azure OpenAI API key is required")
        if not self.azure_openai.deployment_name:
            errors.append("Azure OpenAI deployment name is required")
        
        # Validate file paths
        for folder in [self.file_storage.upload_folder, self.file_storage.output_folder, self.file_storage.temp_folder]:
            try:
                Path(folder).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {folder}: {e}")
        
        # Validate numeric ranges
        if self.azure_openai.temperature < 0 or self.azure_openai.temperature > 2:
            errors.append("Azure OpenAI temperature must be between 0 and 2")
        
        if self.azure_openai.max_tokens < 1:
            errors.append("Azure OpenAI max_tokens must be positive")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "azure_openai": {
                "endpoint": self.azure_openai.endpoint,
                "api_version": self.azure_openai.api_version,
                "deployment_name": self.azure_openai.deployment_name,
                "model_name": self.azure_openai.model_name,
                "temperature": self.azure_openai.temperature,
                "max_tokens": self.azure_openai.max_tokens,
                "top_p": self.azure_openai.top_p
            },
            "application": {
                "name": self.application.name,
                "version": self.application.version,
                "description": self.application.description,
                "debug": self.application.debug,
                "log_level": self.application.log_level
            },
            "file_storage": {
                "upload_folder": self.file_storage.upload_folder,
                "output_folder": self.file_storage.output_folder,
                "temp_folder": self.file_storage.temp_folder,
                "max_file_size_mb": self.file_storage.max_file_size_mb
            },
            "dashboard_generation": {
                "max_worksheets_per_workbook": self.dashboard_generation.max_worksheets_per_workbook,
                "max_dashboards_per_workbook": self.dashboard_generation.max_dashboards_per_workbook,
                "default_width": self.dashboard_generation.default_width,
                "default_height": self.dashboard_generation.default_height,
                "visualization_types": self.dashboard_generation.visualization_types,
                "color_schemes": self.dashboard_generation.color_schemes
            }
        }

# Global configuration instance
_config_instance: Optional[Config] = None

def get_config(config_file: Optional[str] = None, env_file: Optional[str] = None) -> Config:
    """Get the global configuration instance"""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_file, env_file)
    
    return _config_instance

def reset_config():
    """Reset the global configuration instance"""
    global _config_instance
    _config_instance = None