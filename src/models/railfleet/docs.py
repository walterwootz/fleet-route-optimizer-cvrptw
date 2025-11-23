"""
Docs Service models for document management (ECM-Light).
"""
from sqlalchemy import Column, String, DateTime, Enum, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from src.core.database import Base


class DocumentType(str, PyEnum):
    """Document type enumeration."""
    CERTIFICATE = "certificate"
    LICENSE = "license"
    INSPECTION_REPORT = "inspection_report"
    MAINTENANCE_LOG = "maintenance_log"
    TECHNICAL_DRAWING = "technical_drawing"
    COMPLIANCE_DOC = "compliance_doc"
    INVOICE = "invoice"
    CONTRACT = "contract"
    OTHER = "other"


class DocumentStatus(str, PyEnum):
    """Document status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    ARCHIVED = "archived"
    REVOKED = "revoked"


class DocumentLink(Base):
    """Document Link model for ECM-Light document management."""

    __tablename__ = "document_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String(100), unique=True, nullable=False, index=True)

    # Document metadata
    title = Column(String(500), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    description = Column(String(2000), nullable=True)

    # Storage information
    file_url = Column(String(1000), nullable=True)  # External URL or file path
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash for integrity
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Expiration tracking
    issue_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    reminder_days_before = Column(Integer, default=30, nullable=False)  # Days before expiration to alert
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.ACTIVE)

    # Entity associations (what this document relates to)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id", ondelete="SET NULL"), nullable=True)
    workshop_id = Column(UUID(as_uuid=True), ForeignKey("workshops.id", ondelete="SET NULL"), nullable=True)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True)

    # Additional metadata
    tags_json = Column(JSON, nullable=True)  # ["safety", "critical", "regulatory"]
    metadata_json = Column(JSON, nullable=True)  # Additional custom fields

    # Access control
    is_public = Column(Boolean, default=False, nullable=False)
    access_level = Column(String(50), default="internal", nullable=False)  # public, internal, restricted, confidential

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    last_accessed_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<DocumentLink(document_id='{self.document_id}', title='{self.title}', type='{self.document_type}')>"


class DocumentVersion(Base):
    """Document Version model for tracking document history."""

    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_link_id = Column(UUID(as_uuid=True), ForeignKey("document_links.id", ondelete="CASCADE"), nullable=False)

    # Version information
    version_number = Column(Integer, nullable=False)
    version_label = Column(String(50), nullable=True)  # "1.0", "Draft", "Final"
    change_description = Column(String(1000), nullable=True)

    # File information for this version
    file_url = Column(String(1000), nullable=True)
    file_hash = Column(String(64), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<DocumentVersion(document_link_id={self.document_link_id}, version={self.version_number})>"


class DocumentAccessLog(Base):
    """Document Access Log for audit trail."""

    __tablename__ = "document_access_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_link_id = Column(UUID(as_uuid=True), ForeignKey("document_links.id", ondelete="CASCADE"), nullable=False)

    # Access details
    accessed_by = Column(UUID(as_uuid=True), nullable=False)
    access_type = Column(String(50), nullable=False)  # view, download, edit, delete
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamp
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DocumentAccessLog(document_id={self.document_link_id}, type='{self.access_type}', at={self.accessed_at})>"
