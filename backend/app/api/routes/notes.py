import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message, Note, NoteCreate, NotePublic, NotesPublic, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=NotesPublic)
def read_notes(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve notes.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Note)
        count = session.exec(count_statement).one()
        statement = (
            select(Note).order_by(col(Note.created_at).desc()).offset(skip).limit(limit)
        )
        notes = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Note)
            .where(Note.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Note)
            .where(Note.owner_id == current_user.id)
            .order_by(col(Note.created_at).desc())
            .offset(skip)
            .limit(limit)
        )
        notes = session.exec(statement).all()

    notes_public = [NotePublic.model_validate(note) for note in notes]
    return NotesPublic(data=notes_public, count=count)


@router.get("/{id}", response_model=NotePublic)
def read_note(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get note by ID.
    """
    note = session.get(Note, id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not current_user.is_superuser and (note.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return note


@router.post("/", response_model=NotePublic)
def create_note(
    *, session: SessionDep, current_user: CurrentUser, note_in: NoteCreate
) -> Any:
    """
    Create new note.
    """
    note = Note.model_validate(note_in, update={"owner_id": current_user.id})
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


@router.put("/{id}", response_model=NotePublic)
def update_note(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    note_in: NoteUpdate,
) -> Any:
    """
    Update a note.
    """
    note = session.get(Note, id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not current_user.is_superuser and (note.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_dict = note_in.model_dump(exclude_unset=True)
    note.sqlmodel_update(update_dict)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


@router.delete("/{id}")
def delete_note(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a note.
    """
    note = session.get(Note, id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if not current_user.is_superuser and (note.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(note)
    session.commit()
    return Message(message="Note deleted successfully")
