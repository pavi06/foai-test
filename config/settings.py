"""
Configuration management for fo.ai application
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "True").lower() == "true"
    
    # Streamlit Configuration
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_DEFAULT_REGION: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.5"))
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    
    # Application Configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    USERNAME: str = os.getenv("USERNAME", "default_user")
    USE_MOCK_DATA: bool = os.getenv("USE_MOCK_DATA", "False").lower() == "true"
    
    # API URLs
    FOAI_API_URL: str = os.getenv("FOAI_API_URL", "http://localhost:8000")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/foai.log")
    
    # Feature Flags
    ENABLE_STATE_GRAPH: bool = os.getenv("ENABLE_STATE_GRAPH", "True").lower() == "true"
    ENABLE_STREAMING: bool = os.getenv("ENABLE_STREAMING", "True").lower() == "true"
    ENABLE_CHAT_HISTORY: bool = os.getenv("ENABLE_CHAT_HISTORY", "True").lower() == "true"
    
    # Default Preferences
    DEFAULT_PREFERENCES: Dict[str, Any] = {
        "cpu_threshold": 10,
        "min_uptime_hours": 0,
        "min_savings_usd": 0,
        "excluded_tags": ["env=prod", "do-not-touch"],
        "idle_7day_cpu_threshold": 5,
        # S3 preferences
        "s3_standard_to_ia_days": 30,
        "s3_ia_to_glacier_days": 90,
        "s3_glacier_to_deep_archive_days": 180,
        "s3_expiration_days": 2555,
        "s3_excluded_tags": ["environment=prod"],
        "s3_include_previous_versions": False,
        "s3_include_delete_markers": False,
        "s3_min_savings_usd": 1,
        "s3_analyze_versioning": True,
        "s3_analyze_logging": True,
        "s3_analyze_encryption": True
    }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings"""
        required_settings = [
            "REDIS_URL",
            "LLM_MODEL",
            "AWS_REGION"
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not getattr(cls, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"Missing required settings: {missing_settings}")
            return False
        
        return True
    
    @classmethod
    def get_aws_config(cls) -> Dict[str, str]:
        """Get AWS configuration"""
        config = {}
        if cls.AWS_ACCESS_KEY_ID:
            config["aws_access_key_id"] = cls.AWS_ACCESS_KEY_ID
        if cls.AWS_SECRET_ACCESS_KEY:
            config["aws_secret_access_key"] = cls.AWS_SECRET_ACCESS_KEY
        if cls.AWS_DEFAULT_REGION:
            config["region_name"] = cls.AWS_DEFAULT_REGION
        return config
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Get Redis configuration"""
        return {
            "host": cls.REDIS_HOST,
            "port": cls.REDIS_PORT,
            "db": cls.REDIS_DB,
            "decode_responses": True
        }

# Global settings instance
settings = Settings() 