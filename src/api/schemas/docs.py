"""
Docs service schemas for request/response validation.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.models.railfleet.docs import DocumentType, DocumentStatus


class DocumentLinkBase(BaseModel):
    """Base document link schema."""
    document_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    document_type: DocumentType
    description: Optional[str] = Field(None, max_length=2000)
    file_url: Optional[str] = Field(None, max_length=1000)
    file_hash: Optional[str] = Field(None, max_length=64, pattern="^[a-fA-F0-9]{64}$")
    file_size_bytes: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    reminder_days_before: int = Field(30, ge=1, le=365)
    tags_json: Optional[List[str]] = None
    metadata_json: Optional[Dict[str, Any]] = None
    is_public: bool = False
    access_level: str = Field("internal", pattern="^(public|internal|restricted|confidential)$")


class DocumentLinkCreate(DocumentLinkBase):
    """Create document link request."""
    status: DocumentStatus = DocumentStatus.ACTIVE
    vehicle_id: Optional[str] = None
    staff_id: Optional[str] = None
    workshop_id: Optional[str] = None
    work_order_id: Optional[str] = None


class DocumentLinkUpdate(BaseModel):
    """Update document link request (partial updates allowed)."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    document_type: Optional[DocumentType] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_hash: Optional[str] = Field(None, pattern="^[a-fA-F0-9]{64}$")
    file_size_bytes: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    reminder_days_before: Optional[int] = Field(None, ge=1, le=365)
    status: Optional[DocumentStatus] = None
    vehicle_id: Optional[str] = None
    staff_id: Optional[str] = None
    workshop_id: Optional[str] = None
    work_order_id: Optional[str] = None
    tags_json: Optional[List[str]] = None
    metadata_json: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    access_level: Optional[str] = Field(None, pattern="^(public|internal|restricted|confidential)$")


class DocumentLinkResponse(DocumentLinkBase):
    """Document link response."""
    id: str
    status: DocumentStatus
    vehicle_id: Optional[str] = None
    staff_id: Optional[str] = None
    workshop_id: Optional[str] = None
    work_order_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    last_accessed_at: Optional[datetime] = None
    last_accessed_by: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentLinkListResponse(BaseModel):
    """Document links list response."""
    total: int
    documents: List[DocumentLinkResponse]


class ExpiringDocumentResponse(BaseModel):
    """Expiring document response."""
    id: str
    document_id: str
    title: str
    document_type: str
    expiration_date: datetime
    days_until_expiration: float
    expiration_status: str
    vehicle_id: Optional[str] = None
    staff_id: Optional[str] = None
    workshop_id: Optional[str] = None
    work_order_id: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class ExpiringDocumentListResponse(BaseModel):
    """Expiring documents list response."""
    total: int
    documents: List[ExpiringDocumentResponse]


class DocumentVersionBase(BaseModel):
    """Base document version schema."""
    version_number: int = Field(..., ge=1)
    version_label: Optional[str] = Field(None, max_length=50)
    change_description: Optional[str] = Field(None, max_length=1000)
    file_url: Optional[str] = Field(None, max_length=1000)
    file_hash: Optional[str] = Field(None, pattern="^[a-fA-F0-9]{64}$")
    file_size_bytes: Optional[int] = Field(None, ge=0)


class DocumentVersionCreate(DocumentVersionBase):
    """Create document version request."""
    document_link_id: str


class DocumentVersionResponse(DocumentVersionBase):
    """Document version response."""
    id: str
    document_link_id: str
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentVersionListResponse(BaseModel):
    """Document versions list response."""
    total: int
    versions: List[DocumentVersionResponse]


class DocumentAccessLogCreate(BaseModel):
    """Create document access log entry."""
    access_type: str = Field(..., pattern="^(view|download|edit|delete|share)$")
    ip_address: Optional[str] = Field(None, max_length=50)
    user_agent: Optional[str] = Field(None, max_length=500)


class DocumentAccessLogResponse(BaseModel):
    """Document access log response."""
    id: str
    document_link_id: str
    accessed_by: str
    access_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    accessed_at: datetime

    class Config:
        from_attributes = True


class DocumentAccessLogListResponse(BaseModel):
    """Document access log list response."""
    total: int
    access_logs: List[DocumentAccessLogResponse]
