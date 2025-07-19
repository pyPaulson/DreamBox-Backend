from datetime import datetime, timezone
from typing import Annotated, List
from uuid import uuid4
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import user as user_model 
from app.models.goals import MyGoalAccount
from app.schemas import goals


router = APIRouter(prefix="/goals", tags=["Goals"])

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=List[goals.SafeLockResponse])
def get_user_safelocks(
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    safelocks = (
        db.query(user_model.SafeLockAccount)
        .filter(user_model.SafeLockAccount.user_id == current_user.id)
        .all()
    )
    return safelocks



@router.post("/create", response_model=goals.SafeLockResponse)
def create_safelock(
    safelock_data: goals.SafeLockCreate,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    new_safelock = user_model.SafeLockAccount(
        id=uuid4(),
        user_id=current_user.id,
        goal_name=safelock_data.goal_name,
        target_amount=safelock_data.target_amount,
        current_amount=0.0,
        target_date=safelock_data.target_date,
        has_emergency_fund=safelock_data.has_emergency_fund,
        emergency_fund_percentage=safelock_data.emergency_fund_percentage,
        created_at=datetime.now(timezone.utc),
    )

    db.add(new_safelock)
    db.commit()
    db.refresh(new_safelock)

    return new_safelock


@router.post("/create-myGoal", response_model=goals.MyGoalOut)
def create_my_goal(
    goal_data: goals.MyGoalCreate,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user)
):
    new_goal = MyGoalAccount(
        user_id=current_user.id,
        goal_name=goal_data.goal_name,
        target_amount=goal_data.target_amount,
        target_date=goal_data.target_date,
        current_amount=0.0,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal