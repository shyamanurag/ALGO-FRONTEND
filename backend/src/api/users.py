from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..models.user import User, NewUser, UserResponse
from ..core.auth import get_password_hash
from ..core.database import get_db
from ..core.zerodha import ZerodhaClient
from ..core.risk_manager import RiskManager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: NewUser,
    db: Session = Depends(get_db),
    risk_manager: RiskManager = Depends()
):
    """
    Create a new user with proper validation and risk management setup.
    """
    try:
        # Check if username or email already exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user with hashed password
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            initial_capital=user_data.initial_capital,
            risk_tolerance=user_data.risk_tolerance,
            zerodha_client_id=user_data.zerodha_client_id,
            broker_account_id=user_data.broker_account_id,
            trading_enabled=user_data.trading_enabled,
            max_position_size=user_data.max_position_size,
            preferences=user_data.preferences
        )

        # Initialize risk management settings
        await risk_manager.initialize_user_risk_settings(
            user_id=db_user.user_id,
            initial_capital=user_data.initial_capital,
            risk_tolerance=user_data.risk_tolerance,
            max_position_size=user_data.max_position_size
        )

        # Save to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"Created new user: {db_user.username}")
        return UserResponse.from_orm(db_user)

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        ) 