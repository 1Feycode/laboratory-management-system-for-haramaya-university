import argparse
import asyncio
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import AsyncSessionFactory, engine
from app.models.user import Role, User
from app.schemas.user import UserCreate


async def create_initial_admin() -> None:
    email = input("Institutional email: ").strip().casefold()
    full_name = input("Full name: ").strip()
    password = getpass("Password (10+ characters, letters and digits): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    try:
        payload = UserCreate(
            email=email,
            full_name=full_name,
            password=password,
            role="ULMD_ADMIN",
            department_id=None,
        )
    except ValidationError:
        raise SystemExit(
            "Invalid account details. Check the email, name, and password policy."
        ) from None

    async with AsyncSessionFactory() as session:
        active_admins = await session.scalar(
            select(func.count(User.id))
            .join(Role, User.role_id == Role.id)
            .where(Role.name == "ULMD_ADMIN", User.is_active.is_(True))
        )
        if active_admins:
            raise SystemExit("An active ULMD_ADMIN already exists.")
        role = await session.scalar(select(Role).where(Role.name == "ULMD_ADMIN"))
        if role is None:
            raise SystemExit("Roles are not seeded; run Alembic migrations first.")
        user = User(
            email=str(payload.email).casefold(),
            hashed_password=hash_password(payload.password.get_secret_value()),
            full_name=payload.full_name,
            role=role,
        )
        session.add(user)
        await session.commit()
        print(f"Created initial ULMD_ADMIN account: {user.email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Laboratory system administration")
    parser.add_argument("command", choices=["create-admin"])
    args = parser.parse_args()
    try:
        if args.command == "create-admin":
            asyncio.run(create_initial_admin())
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
