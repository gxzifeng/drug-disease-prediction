import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def create_or_update_admin():
    async with AsyncSessionLocal() as session:
        # 检查admin用户是否已存在
        result = await session.execute(select(User).where(User.username == 'admin'))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"📋 用户 '{user.username}' 已存在")
            print(f"   邮箱: {user.email}")
            print(f"   是否超级用户: {user.is_superuser}")
            print(f"   是否激活: {user.is_active}")
            
            # 更新密码
            old_hash = user.hashed_password[:30] + '...' if user.hashed_password else '无'
            user.hashed_password = get_password_hash('admin123')
            await session.commit()
            
            print(f"🔄 密码已更新")
            print(f"   旧哈希: {old_hash}")
            print(f"   新密码: 'admin123'")
        else:
            print("🆕 创建新的admin用户")
            admin = User(
                username='admin',
                email='admin@example.com',
                hashed_password=get_password_hash('admin123'),
                is_superuser=True,
                is_active=True,
                full_name='Administrator'
            )
            session.add(admin)
            await session.commit()
            
            print("✅ 用户创建成功")
            print(f"   用户名: admin")
            print(f"   密码: admin123")
            print(f"   邮箱: admin@example.com")
        
        # 显示所有用户
        print("\\n👥 当前所有用户:")
        result = await session.execute(select(User))
        users = result.scalars().all()
        for u in users:
            status = '🟢' if u.is_active else '🔴'
            super_status = '👑' if u.is_superuser else '👤'
            print(f"   {status}{super_status} {u.username} ({u.email})")

if __name__ == '__main__':
    asyncio.run(create_or_update_admin())
