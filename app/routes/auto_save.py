from typing import Annotated, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import user as user_model
from app.models.wallets import Wallet
from app.models.goals import SafeLockAccount, MyGoalAccount
from app.models.auto_save import AutoSaveSetting, AutoSaveTransaction
from app.schemas.auto_save import (
    AutoSaveCreate,
    AutoSaveUpdate,
    AutoSaveResponse,
    AutoSaveTransactionListResponse,
    MessageResponse
)

router = APIRouter(prefix="/auto-save", tags=["Auto-Save"])

db_dependency = Annotated[Session, Depends(get_db)]


def calculate_next_execution(frequency: str, time: datetime.time) -> datetime:
    """Calculate the next execution time based on frequency and time"""
    now = datetime.now()
    today = now.date()
    
    # Create datetime for today with the specified time
    next_execution = datetime.combine(today, time)
    
    # If the time has already passed today, schedule for next occurrence
    if next_execution <= now:
        if frequency == "daily":
            next_execution += timedelta(days=1)
        elif frequency == "weekly":
            next_execution += timedelta(weeks=1)
        elif frequency == "monthly":
            # Add one month, handling month boundaries
            if next_execution.month == 12:
                next_execution = next_execution.replace(year=next_execution.year + 1, month=1)
            else:
                next_execution = next_execution.replace(month=next_execution.month + 1)
    
    return next_execution


@router.post("/goals/{goal_id}/auto-save", response_model=AutoSaveResponse, status_code=status.HTTP_201_CREATED)
def create_auto_save(
    goal_id: UUID,
    auto_save_data: AutoSaveCreate,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    """Create auto-save setting for a goal"""
    
    # Verify goal exists and belongs to user (check both SafeLock and MyGoal)
    goal = (
        db.query(SafeLockAccount)
        .filter(
            and_(
                SafeLockAccount.id == goal_id,
                SafeLockAccount.user_id == current_user.id
            )
        )
        .first()
    )
    
    if not goal:
        goal = (
            db.query(MyGoalAccount)
            .filter(
                and_(
                    MyGoalAccount.id == goal_id,
                    MyGoalAccount.user_id == current_user.id
                )
            )
            .first()
        )
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Check if goal already has an auto-save setting
    existing_auto_save = (
        db.query(AutoSaveSetting)
        .filter(AutoSaveSetting.goal_id == goal_id)
        .first()
    )
    
    if existing_auto_save:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auto-save setting already exists for this goal"
        )
    
    # Verify wallet exists and belongs to user
    wallet = (
        db.query(Wallet)
        .filter(
            and_(
                Wallet.id == auto_save_data.wallet_id,
                Wallet.user_id == current_user.id
            )
        )
        .first()
    )
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Check user's auto-save limit (max 10 per user)
    user_auto_save_count = (
        db.query(AutoSaveSetting)
        .filter(AutoSaveSetting.user_id == current_user.id)
        .count()
    )
    
    if user_auto_save_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 10 auto-save settings allowed per user"
        )
    
    # Calculate next execution time
    next_execution = calculate_next_execution(auto_save_data.frequency, auto_save_data.time)
    
    # Determine goal type
    goal_type = 'safelock' if isinstance(goal, SafeLockAccount) else 'mygoal'
    
    new_auto_save = AutoSaveSetting(
        goal_id=goal_id,
        goal_type=goal_type,
        user_id=current_user.id,
        wallet_id=auto_save_data.wallet_id,
        frequency=auto_save_data.frequency,
        time=auto_save_data.time,
        amount=auto_save_data.amount,
        next_execution=next_execution
    )
    
    db.add(new_auto_save)
    db.commit()
    db.refresh(new_auto_save)
    
    return new_auto_save


@router.put("/goals/{goal_id}/auto-save", response_model=AutoSaveResponse)
def update_auto_save(
    goal_id: UUID,
    auto_save_data: AutoSaveUpdate,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    """Update auto-save setting for a goal"""
    
    # Verify goal exists and belongs to user (check both SafeLock and MyGoal)
    goal = (
        db.query(SafeLockAccount)
        .filter(
            and_(
                SafeLockAccount.id == goal_id,
                SafeLockAccount.user_id == current_user.id
            )
        )
        .first()
    )
    
    if not goal:
        goal = (
            db.query(MyGoalAccount)
            .filter(
                and_(
                    MyGoalAccount.id == goal_id,
                    MyGoalAccount.user_id == current_user.id
                )
            )
            .first()
        )
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Get existing auto-save setting
    auto_save = (
        db.query(AutoSaveSetting)
        .filter(AutoSaveSetting.goal_id == goal_id)
        .first()
    )
    
    if not auto_save:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auto-save setting not found for this goal"
        )
    
    # Verify wallet exists and belongs to user (if updating wallet)
    if auto_save_data.wallet_id:
        wallet = (
            db.query(Wallet)
            .filter(
                and_(
                    Wallet.id == auto_save_data.wallet_id,
                    Wallet.user_id == current_user.id
                )
            )
            .first()
        )
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found"
            )
    
    # Update fields
    update_data = auto_save_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(auto_save, field, value)
    
    # Recalculate next execution if frequency or time changed
    if auto_save_data.frequency or auto_save_data.time:
        frequency = auto_save_data.frequency or auto_save.frequency
        time = auto_save_data.time or auto_save.time
        auto_save.next_execution = calculate_next_execution(frequency, time)
    
    db.commit()
    db.refresh(auto_save)
    
    return auto_save


@router.delete("/goals/{goal_id}/auto-save", response_model=MessageResponse)
def delete_auto_save(
    goal_id: UUID,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    """Delete auto-save setting for a goal"""
    
    # Verify goal exists and belongs to user (check both SafeLock and MyGoal)
    goal = (
        db.query(SafeLockAccount)
        .filter(
            and_(
                SafeLockAccount.id == goal_id,
                SafeLockAccount.user_id == current_user.id
            )
        )
        .first()
    )
    
    if not goal:
        goal = (
            db.query(MyGoalAccount)
            .filter(
                and_(
                    MyGoalAccount.id == goal_id,
                    MyGoalAccount.user_id == current_user.id
                )
            )
            .first()
        )
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Get existing auto-save setting
    auto_save = (
        db.query(AutoSaveSetting)
        .filter(AutoSaveSetting.goal_id == goal_id)
        .first()
    )
    
    if not auto_save:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auto-save setting not found for this goal"
        )
    
    db.delete(auto_save)
    db.commit()
    
    return MessageResponse(message="Auto-save disabled successfully")


@router.get("/goals/{goal_id}/auto-save", response_model=AutoSaveResponse)
def get_auto_save(
    goal_id: UUID,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    """Get auto-save setting for a goal"""
    
    # Verify goal exists and belongs to user (check both SafeLock and MyGoal)
    goal = (
        db.query(SafeLockAccount)
        .filter(
            and_(
                SafeLockAccount.id == goal_id,
                SafeLockAccount.user_id == current_user.id
            )
        )
        .first()
    )
    
    if not goal:
        goal = (
            db.query(MyGoalAccount)
            .filter(
                and_(
                    MyGoalAccount.id == goal_id,
                    MyGoalAccount.user_id == current_user.id
                )
            )
            .first()
        )
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Get auto-save setting
    auto_save = (
        db.query(AutoSaveSetting)
        .filter(AutoSaveSetting.goal_id == goal_id)
        .first()
    )
    
    if not auto_save:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auto-save setting not found for this goal"
        )
    
    return auto_save


@router.get("/transactions", response_model=AutoSaveTransactionListResponse)
def get_auto_save_transactions(
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
    goal_id: Optional[UUID] = Query(None, description="Filter by goal ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
):
    """Get auto-save transaction history"""
    
    query = (
        db.query(AutoSaveTransaction)
        .join(AutoSaveSetting)
        .filter(AutoSaveSetting.user_id == current_user.id)
    )
    
    if goal_id:
        # Verify goal belongs to user
        goal = (
            db.query(SafeLockAccount)
            .filter(
                and_(
                    SafeLockAccount.id == goal_id,
                    SafeLockAccount.user_id == current_user.id
                )
            )
            .first()
        )
        
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        
        query = query.filter(AutoSaveTransaction.goal_id == goal_id)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    transactions = (
        query
        .order_by(desc(AutoSaveTransaction.executed_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return AutoSaveTransactionListResponse(
        transactions=transactions,
        total=total,
        limit=limit,
        offset=offset
    )
