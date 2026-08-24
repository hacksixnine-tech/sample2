from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "PHANTOM Video Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Regional & Distributed Topology
    NODE_ROLE: str = "CENTRAL"  # CENTRAL, REGIONAL_GATEWAY, EDGE_NODE
    REGIONAL_ZONE: str = "CENTRAL_GUJARAT"  # e.g. NORTH_GUJARAT, CENTRAL_GUJARAT, SOUTH_GUJARAT, SAURASHTRA, KUTCH
    REGIONAL_GATEWAY_URL: Optional[str] = None

    # Security & JWT
    SECRET_KEY: str = "phantom_development_default_secret_key_2026_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS & Allowed Hosts
    ALLOWED_HOSTS: Union[List[str], str] = ["*"]
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]

    # Database Settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "phantom"
    POSTGRES_USER: str = "phantom_app"
    POSTGRES_PASSWORD: str = "phantom_app_secure_password_2026"
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://phantom_app:phantom_app_secure_password_2026@localhost:5432/phantom"
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://phantom_app:phantom_app_secure_password_2026@localhost:5432/phantom"
    )
    DB_READ_REPLICA_URL: Optional[str] = None

    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # Object Storage (S3 / MinIO - Evidence & Snapshot Store)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "phantom-evidence"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    # Redis & Kafka (Future Messaging & Distributed Caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    WEBSOCKET_MAX_CLIENTS: int = 5000

    # Stream Profile & Bandwidth Management
    STREAM_PROFILE_DEFAULT: str = "MEDIUM"
    STREAM_LOW_RES: str = "640x480"
    STREAM_LOW_FPS: int = 15
    STREAM_LOW_BITRATE_KBPS: int = 500

    STREAM_MEDIUM_RES: str = "1280x720"
    STREAM_MEDIUM_FPS: int = 20
    STREAM_MEDIUM_BITRATE_KBPS: int = 1500

    STREAM_HIGH_RES: str = "1920x1080"
    STREAM_HIGH_FPS: int = 25
    STREAM_HIGH_BITRATE_KBPS: int = 4000

    STREAM_BURST_RES: str = "1920x1080"
    STREAM_BURST_FPS: int = 30
    STREAM_BURST_BITRATE_KBPS: int = 6000

    # Stream Gateway & Live CCTV Transcoding / Proxying
    STREAM_GATEWAY_CACHE_DIR: str = "./var/hls_cache"
    STREAM_FFMPEG_BIN: str = "ffmpeg"
    CAMERA_SOURCES_FILE: str = "camera_sources.yaml"
    ENABLE_TEST_STREAM_FALLBACK: bool = True
    STREAM_GATEWAY_TIMEOUT_SECONDS: int = 8
    HLS_SEGMENT_DURATION_SECONDS: int = 2
    HLS_LIST_SIZE: int = 4

    # Edge Buffering & Offline Resilience
    EDGE_BUFFER_ENABLED: bool = True
    EDGE_BUFFER_RETENTION_HOURS: int = 24
    EDGE_BUFFER_MAX_MB: int = 10240

    # Health Aggregation Hierarchy
    HEALTH_AGGREGATION_INTERVAL_SECONDS: int = 15
    HEALTH_HEARTBEAT_TIMEOUT_SECONDS: int = 45

    # AI Analytics & Inference Scaling
    DEMO_AI_MODE: bool = False
    AI_WORKER_API_KEY: str = "phantom_ai_worker_dev_key_2026"
    AI_INGEST_MAX_BYTES: int = 1048576
    AI_INGEST_MAX_DETECTIONS: int = 50
    AI_MODEL_NAME: str = "yolov8n"
    AI_MODEL_VERSION: str = "os-compat-0.1.0"
    AI_MODEL_PATH: str = ""
    AI_CONFIDENCE_THRESHOLD: float = 0.35
    AI_IOU_THRESHOLD: float = 0.45
    AI_OCR_THRESHOLD: float = 0.60
    AI_FRAME_INTERVAL_FPS: float = 2.0  # Configurable sampling rate (2-5 FPS default)
    AI_DEVICE: str = "cpu"
    AI_DEDUPE_WINDOW_SECONDS: float = 2.0
    EVIDENCE_STORAGE_BACKEND: str = "filesystem"
    EVIDENCE_LOCAL_ROOT: str = "./var/evidence"
    EVIDENCE_RETENTION_DAYS: int = 30

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() in ("development", "dev", "local")


settings = Settings()
