"""Dev ingress — a webhook stand-in for the prototype."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import inbox as inbox_service, schemas
from ..auth import Principal, get_db, require_account
from ..models import Account, Repo

router = APIRouter(prefix="/v1/_dev", tags=["dev"])


@router.post("/enqueue", status_code=status.HTTP_201_CREATED, response_model=schemas.DevEnqueued)
def enqueue(payload: schemas.DevEnqueue, principal: Principal = Depends(require_account), db: Session = Depends(get_db)):
    repo = db.execute(select(Repo).where(Repo.id == payload.repo_id, Repo.account_id == principal.account_id)).scalar_one_or_none()
    if repo is None:
        raise HTTPException(status_code=404, detail="repo not found")
    source = payload.source.strip() or "dev"
    if source.casefold() == "hosted":
        account = db.get(Account, principal.account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="account not found")
        if account.hosted_exec_terms_accepted_at is None:
            if not payload.accept_hosted_execution_terms:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="hosted execution terms must be accepted before the first hosted run",
                )
            account.hosted_exec_terms_accepted_at = datetime.now(timezone.utc)
            db.add(account)
            db.commit()
    event = inbox_service.enqueue(db, repo_id=repo.id, body=payload.body, source=source, reply_to=payload.reply_to)
    return schemas.DevEnqueued(event_id=event.event_id, seq=event.seq)
