import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.tenant import Tenant
from src.db.models.user import User
from src.db.session import get_db_session, get_db_session_with_tenant
from src.integrations.kafka_producer import TypedKafkaProducer
from src.integrations.langfuse_client import LangfuseTracer
from src.integrations.llm_client import GeminiLLMClient
from src.integrations.minio_client import ObjectStoreClient
from src.integrations.qdrant_client import QdrantVectorStore
from src.integrations.redis_client import RedisClient

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

def get_redis(request: Request) -> RedisClient:
    return request.app.state.redis

def get_kafka_producer(request: Request) -> TypedKafkaProducer:
    return request.app.state.kafka

def get_qdrant(request: Request) -> QdrantVectorStore:
    return request.app.state.qdrant

def get_llm(request: Request) -> GeminiLLMClient:
    return request.app.state.llm

def get_langfuse(request: Request) -> LangfuseTracer:
    return request.app.state.langfuse

def get_object_store(request: Request) -> ObjectStoreClient:
    return request.app.state.minio

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> User:
    try:
        user_id = uuid.UUID(token)
        stmt = select(User).where(User.id == user_id)
    except ValueError:
        stmt = select(User).where(User.email == token)

    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_tenant(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> Tenant:
    stmt = select(Tenant).where(Tenant.id == user.tenant_id)
    result = await session.execute(stmt)
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant not found")
    return tenant

async def get_rls_session(
    tenant: Annotated[Tenant, Depends(get_current_tenant)]
):
    async for session in get_db_session_with_tenant(tenant.id):
        yield session
