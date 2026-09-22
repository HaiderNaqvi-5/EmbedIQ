import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, HttpUrl, Field
from app.schemas.brand import BrandSettingsResponse


class BotCreateRequest(BaseModel):
    website_url: str = Field(..., description="Target website URL to crawl and index")
    name: Optional[str] = Field(None, description="Chatbot name (defaults to domain if not provided)")


class BotResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    website_url: str
    normalized_origin: str
    status: str
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotCreateResponse(BaseModel):
    bot_id: uuid.UUID
    job_id: uuid.UUID
    name: str
    website_url: str
    status: str
    created_at: datetime


class BotDetailResponse(BotResponse):
    branding: Optional[BrandSettingsResponse] = None
    total_pages_indexed: int = 0
    total_chunks: int = 0


class CrawlStatusResponse(BaseModel):
    bot_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    status: str
    stage: str
    total_pages: int
    processed_pages: int
    failed_pages: int
    warning_count: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class KnowledgeResponse(BaseModel):
    bot_id: uuid.UUID
    document_id: Optional[uuid.UUID] = None
    markdown_content: Optional[str] = None
    chunk_count: int = 0
    last_indexed_at: Optional[datetime] = None
