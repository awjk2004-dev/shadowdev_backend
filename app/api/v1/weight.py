from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from decimal import Decimal

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.player import Player, sync_player_progress
from app.models.weight_entry import WeightEntry
from app.schemas.weight import WeightEntryCreate, WeightEntryResponse

router = APIRouter()

@router.post("", response_model=WeightEntryResponse)
async def record_weight(
    weight_in: WeightEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تسجيل وزن جديد وإعطاء XP لكل 0.5 كجم زيادة"""
    # 1. جلب بيانات اللاعب
    player_result = await db.execute(
        select(Player)
        .where(Player.user_id == current_user.id)
        .with_for_update()
    )
    player = player_result.scalars().first()
    
    # 2. حساب الفرق
    current_weight = float(player.current_weight or 0)
    diff = float(weight_in.weight) - current_weight
    xp_awarded = 0

    if current_weight > 0:
        if diff >= 0.5:
            # كل 0.5 كجم = 100 XP
            units = int(diff / 0.5)
            xp_awarded = units * 100
            player.xp += xp_awarded
    else:
        # أول وزن يسجله المستخدم: نعتبره وزن البداية دون منح XP
        player.start_weight = weight_in.weight

    # 3. تحديث وزن اللاعب الحالي ومزامنة المستوى والرتبة
    player.current_weight = weight_in.weight
    sync_player_progress(player)
    
    # 4. حفظ السجل
    new_entry = WeightEntry(
        user_id=current_user.id,
        weight=weight_in.weight,
        xp_awarded=xp_awarded
    )
    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)
    
    return new_entry