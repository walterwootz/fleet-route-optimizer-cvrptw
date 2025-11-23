"""
Docs service endpoints for document management (ECM-Light).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from src.core.database import get_db
from src.models.railfleet.docs import (
    DocumentLink,
    DocumentVersion,
    DocumentAccessLog,
    DocumentType,
    DocumentStatus,
)
from src.api.schemas.docs import (
    DocumentLinkCreate,
    DocumentLinkUpdate,
    DocumentLinkResponse,
    DocumentLinkListResponse,
    ExpiringDocumentResponse,
    ExpiringDocumentListResponse,
    DocumentVersionCreate,
    DocumentVersionResponse,
    DocumentVersionListResponse,
    DocumentAccessLogCreate,
    DocumentAccessLogResponse,
    DocumentAccessLogListResponse,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/docs", tags=["Documents"])


# Document Links
@router.post("/links", response_model=DocumentLinkResponse, status_code=status.HTTP_201_CREATED)
def create_document_link(
    doc_data: DocumentLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new document link."""
    # Check if document_id already exists
    if db.query(DocumentLink).filter(DocumentLink.document_id == doc_data.document_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document with document_id '{doc_data.document_id}' already exists",
        )

    # Convert entity IDs to UUIDs if provided
    vehicle_id = UUID(doc_data.vehicle_id) if doc_data.vehicle_id else None
    staff_id = UUID(doc_data.staff_id) if doc_data.staff_id else None
    workshop_id = UUID(doc_data.workshop_id) if doc_data.workshop_id else None
    work_order_id = UUID(doc_data.work_order_id) if doc_data.work_order_id else None

    new_doc = DocumentLink(
        **doc_data.model_dump(exclude={"vehicle_id", "staff_id", "workshop_id", "work_order_id"}),
        vehicle_id=vehicle_id,
        staff_id=staff_id,
        workshop_id=workshop_id,
        work_order_id=work_order_id,
        created_by=current_user.id,
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return DocumentLinkResponse(
        id=str(new_doc.id),
        **{k: v for k, v in new_doc.__dict__.items() if not k.startswith("_")},
    )


@router.get("/links", response_model=DocumentLinkListResponse)
def list_document_links(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    document_type: Optional[DocumentType] = None,
    status: Optional[DocumentStatus] = None,
    vehicle_id: Optional[UUID] = None,
    staff_id: Optional[UUID] = None,
    workshop_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all document links with optional filtering."""
    query = db.query(DocumentLink)

    if document_type:
        query = query.filter(DocumentLink.document_type == document_type)

    if status:
        query = query.filter(DocumentLink.status == status)

    if vehicle_id:
        query = query.filter(DocumentLink.vehicle_id == vehicle_id)

    if staff_id:
        query = query.filter(DocumentLink.staff_id == staff_id)

    if workshop_id:
        query = query.filter(DocumentLink.workshop_id == workshop_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (DocumentLink.document_id.ilike(search_pattern))
            | (DocumentLink.title.ilike(search_pattern))
            | (DocumentLink.description.ilike(search_pattern))
        )

    total = query.count()
    documents = query.order_by(DocumentLink.created_at.desc()).offset(skip).limit(limit).all()

    return DocumentLinkListResponse(
        total=total,
        documents=[
            DocumentLinkResponse(
                id=str(d.id),
                **{k: v for k, v in d.__dict__.items() if not k.startswith("_")},
            )
            for d in documents
        ],
    )


@router.get("/links/{doc_id}", response_model=DocumentLinkResponse)
def get_document_link(
    doc_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific document link by ID."""
    doc = db.query(DocumentLink).filter(DocumentLink.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found",
        )

    # Log access
    access_log = DocumentAccessLog(
        document_link_id=doc_id,
        accessed_by=current_user.id,
        access_type="view",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(access_log)

    # Update last accessed
    doc.last_accessed_at = datetime.utcnow()
    doc.last_accessed_by = current_user.id
    db.commit()

    return DocumentLinkResponse(
        id=str(doc.id),
        **{k: v for k, v in doc.__dict__.items() if not k.startswith("_")},
    )


@router.patch("/links/{doc_id}", response_model=DocumentLinkResponse)
def update_document_link(
    doc_id: UUID,
    doc_update: DocumentLinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a document link."""
    doc = db.query(DocumentLink).filter(DocumentLink.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found",
        )

    # Update fields
    update_data = doc_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in ["vehicle_id", "staff_id", "workshop_id", "work_order_id"] and value:
            value = UUID(value)
        setattr(doc, key, value)

    db.commit()
    db.refresh(doc)

    return DocumentLinkResponse(
        id=str(doc.id),
        **{k: v for k, v in doc.__dict__.items() if not k.startswith("_")},
    )


@router.delete("/links/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_link(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document link."""
    doc = db.query(DocumentLink).filter(DocumentLink.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found",
        )

    db.delete(doc)
    db.commit()


# Expiring Documents
@router.get("/expiring", response_model=ExpiringDocumentListResponse)
def list_expiring_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    expiration_status: Optional[str] = Query(None, pattern="^(expired|expiring_soon|ok)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents expiring soon or already expired."""
    query = db.query(text("SELECT * FROM v_expiring_documents"))

    # Execute query
    result = db.execute(text("SELECT * FROM v_expiring_documents"))
    all_docs = result.fetchall()

    # Filter by expiration status if provided
    if expiration_status:
        all_docs = [doc for doc in all_docs if doc.expiration_status == expiration_status]

    total = len(all_docs)
    documents = all_docs[skip : skip + limit]

    return ExpiringDocumentListResponse(
        total=total,
        documents=[
            ExpiringDocumentResponse(
                id=str(doc.id),
                document_id=doc.document_id,
                title=doc.title,
                document_type=doc.document_type,
                expiration_date=doc.expiration_date,
                days_until_expiration=doc.days_until_expiration.days if doc.days_until_expiration else 0,
                expiration_status=doc.expiration_status,
                vehicle_id=str(doc.vehicle_id) if doc.vehicle_id else None,
                staff_id=str(doc.staff_id) if doc.staff_id else None,
                workshop_id=str(doc.workshop_id) if doc.workshop_id else None,
                work_order_id=str(doc.work_order_id) if doc.work_order_id else None,
                status=doc.status,
            )
            for doc in documents
        ],
    )


# Document Versions
@router.post("/versions", response_model=DocumentVersionResponse, status_code=status.HTTP_201_CREATED)
def create_document_version(
    version_data: DocumentVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new document version."""
    try:
        document_link_id = UUID(version_data.document_link_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for document_link_id",
        )

    # Verify document exists
    doc = db.query(DocumentLink).filter(DocumentLink.id == document_link_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_link_id} not found",
        )

    # Check if version already exists
    existing_version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_link_id == document_link_id,
            DocumentVersion.version_number == version_data.version_number,
        )
        .first()
    )
    if existing_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Version {version_data.version_number} already exists for this document",
        )

    new_version = DocumentVersion(
        **version_data.model_dump(exclude={"document_link_id"}),
        document_link_id=document_link_id,
        created_by=current_user.id,
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return DocumentVersionResponse(
        id=str(new_version.id),
        **{k: v for k, v in new_version.__dict__.items() if not k.startswith("_")},
    )


@router.get("/links/{doc_id}/versions", response_model=DocumentVersionListResponse)
def list_document_versions(
    doc_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List versions for a document."""
    query = db.query(DocumentVersion).filter(DocumentVersion.document_link_id == doc_id)

    total = query.count()
    versions = query.order_by(DocumentVersion.version_number.desc()).offset(skip).limit(limit).all()

    return DocumentVersionListResponse(
        total=total,
        versions=[
            DocumentVersionResponse(
                id=str(v.id),
                **{k: val for k, val in v.__dict__.items() if not k.startswith("_")},
            )
            for v in versions
        ],
    )


# Document Access Log
@router.get("/links/{doc_id}/access-log", response_model=DocumentAccessLogListResponse)
def list_document_access_log(
    doc_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List access log for a document."""
    query = db.query(DocumentAccessLog).filter(DocumentAccessLog.document_link_id == doc_id)

    total = query.count()
    logs = query.order_by(DocumentAccessLog.accessed_at.desc()).offset(skip).limit(limit).all()

    return DocumentAccessLogListResponse(
        total=total,
        access_logs=[
            DocumentAccessLogResponse(
                id=str(log.id),
                **{k: v for k, v in log.__dict__.items() if not k.startswith("_")},
            )
            for log in logs
        ],
    )
