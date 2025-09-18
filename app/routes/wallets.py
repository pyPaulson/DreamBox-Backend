from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import user as user_model
from app.models.wallets import Wallet
from app.schemas.wallets import (
    WalletCreate, 
    WalletUpdate, 
    WalletResponse, 
    WalletListResponse, 
    MessageResponse
)

router = APIRouter(prefix="/wallets", tags=["Wallets"])

db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=WalletListResponse)
def get_user_wallets(
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    """Get all wallets for the authenticated user"""
    wallets = (
        db.query(Wallet)
        .filter(Wallet.user_id == current_user.id)
        .order_by(Wallet.is_default.desc(), Wallet.created_at.desc())
        .all()
    )
    return WalletListResponse(wallets=wallets)


@router.post("/", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def create_wallet(
    wallet_data: WalletCreate,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    """Create a new wallet for the authenticated user"""
    
    # Check if wallet with same phone number and provider already exists for user
    existing_wallet = (
        db.query(Wallet)
        .filter(
            and_(
                Wallet.user_id == current_user.id,
                Wallet.phone_number == wallet_data.phone_number,
                Wallet.provider == wallet_data.provider
            )
        )
        .first()
    )
    
    if existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet with this phone number and provider already exists"
        )
    
    # If this is set as default, unset other default wallets
    if wallet_data.is_default:
        db.query(Wallet).filter(
            and_(
                Wallet.user_id == current_user.id,
                Wallet.is_default == True
            )
        ).update({"is_default": False})
    
    new_wallet = Wallet(
        user_id=current_user.id,
        provider=wallet_data.provider,
        phone_number=wallet_data.phone_number,
        account_name=wallet_data.account_name,
        is_default=wallet_data.is_default
    )
    
    db.add(new_wallet)
    db.commit()
    db.refresh(new_wallet)
    
    return new_wallet


@router.put("/{wallet_id}", response_model=WalletResponse)
def update_wallet(
    wallet_id: UUID,
    wallet_data: WalletUpdate,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    """Update an existing wallet"""
    
    wallet = (
        db.query(Wallet)
        .filter(
            and_(
                Wallet.id == wallet_id,
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
    
    # Check if updating phone number and provider combination already exists
    if wallet_data.phone_number and wallet_data.provider:
        existing_wallet = (
            db.query(Wallet)
            .filter(
                and_(
                    Wallet.user_id == current_user.id,
                    Wallet.phone_number == wallet_data.phone_number,
                    Wallet.provider == wallet_data.provider,
                    Wallet.id != wallet_id
                )
            )
            .first()
        )
        
        if existing_wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet with this phone number and provider already exists"
            )
    
    # If setting as default, unset other default wallets
    if wallet_data.is_default:
        db.query(Wallet).filter(
            and_(
                Wallet.user_id == current_user.id,
                Wallet.is_default == True,
                Wallet.id != wallet_id
            )
        ).update({"is_default": False})
    
    # Update wallet fields
    update_data = wallet_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wallet, field, value)
    
    db.commit()
    db.refresh(wallet)
    
    return wallet


@router.delete("/{wallet_id}", response_model=MessageResponse)
def delete_wallet(
    wallet_id: UUID,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    """Delete a wallet"""
    
    wallet = (
        db.query(Wallet)
        .filter(
            and_(
                Wallet.id == wallet_id,
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
    
    # Check if wallet is being used in any active auto-save settings
    from app.models.auto_save import AutoSaveSetting
    active_auto_saves = (
        db.query(AutoSaveSetting)
        .filter(
            and_(
                AutoSaveSetting.wallet_id == wallet_id,
                AutoSaveSetting.is_active == True
            )
        )
        .count()
    )
    
    if active_auto_saves > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete wallet that is being used in active auto-save settings"
        )
    
    db.delete(wallet)
    db.commit()
    
    return MessageResponse(message="Wallet deleted successfully")


@router.put("/{wallet_id}/set-default", response_model=MessageResponse)
def set_default_wallet(
    wallet_id: UUID,
    db: db_dependency,
    current_user: user_model.User = Depends(get_current_user),
):
    """Set a wallet as the default wallet for the user"""
    
    wallet = (
        db.query(Wallet)
        .filter(
            and_(
                Wallet.id == wallet_id,
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
    
    # Unset all other default wallets for this user
    db.query(Wallet).filter(
        and_(
            Wallet.user_id == current_user.id,
            Wallet.is_default == True
        )
    ).update({"is_default": False})
    
    # Set this wallet as default
    wallet.is_default = True
    db.commit()
    
    return MessageResponse(message="Default wallet updated successfully")
