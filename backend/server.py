"""FastAPI server exposing AI agent endpoints."""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Request, File, UploadFile
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
import base64

from ai_agents.agents import AgentConfig, ChatAgent, SearchAgent


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent


class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


class ChatRequest(BaseModel):
    message: str
    agent_type: str = "chat"
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    agent_type: str
    capabilities: List[str]
    metadata: dict = Field(default_factory=dict)
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResponse(BaseModel):
    success: bool
    query: str
    summary: str
    search_results: Optional[dict] = None
    sources_count: int
    error: Optional[str] = None


class Article(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    summary: str = ""
    category: str
    author: str = "Admin"
    image_url: str = ""
    image_data: str = ""  # Base64 encoded image
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    views: int = 0
    shares: int = 0
    published: bool = True


class ArticleCreate(BaseModel):
    title: str
    content: str
    category: str
    author: Optional[str] = "Admin"
    image_url: Optional[str] = ""
    image_data: Optional[str] = ""
    published: Optional[bool] = True


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    image_data: Optional[str] = None
    published: Optional[bool] = None


class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""


def _ensure_db(request: Request):
    try:
        return request.app.state.db
    except AttributeError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=503, detail="Database not ready") from exc


def _get_agent_cache(request: Request) -> Dict[str, object]:
    if not hasattr(request.app.state, "agent_cache"):
        request.app.state.agent_cache = {}
    return request.app.state.agent_cache


async def _get_or_create_agent(request: Request, agent_type: str):
    cache = _get_agent_cache(request)
    if agent_type in cache:
        return cache[agent_type]

    config: AgentConfig = request.app.state.agent_config

    if agent_type == "search":
        cache[agent_type] = SearchAgent(config)
    elif agent_type == "chat":
        cache[agent_type] = ChatAgent(config)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown agent type '{agent_type}'")

    return cache[agent_type]


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(ROOT_DIR / ".env")

    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME")

    if not mongo_url or not db_name:
        missing = [name for name, value in {"MONGO_URL": mongo_url, "DB_NAME": db_name}.items() if not value]
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    client = AsyncIOMotorClient(mongo_url)

    try:
        app.state.mongo_client = client
        app.state.db = client[db_name]
        app.state.agent_config = AgentConfig()
        app.state.agent_cache = {}
        logger.info("AI Agents API starting up")
        yield
    finally:
        client.close()
        logger.info("AI Agents API shutdown complete")


app = FastAPI(
    title="AI Agents API",
    description="Minimal AI Agents API with LangGraph and MCP support",
    lifespan=lifespan,
)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "Hello World"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate, request: Request):
    db = _ensure_db(request)
    status_obj = StatusCheck(**input.model_dump())
    await db.status_checks.insert_one(status_obj.model_dump())
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks(request: Request):
    db = _ensure_db(request)
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_request: ChatRequest, request: Request):
    try:
        agent = await _get_or_create_agent(request, chat_request.agent_type)
        response = await agent.execute(chat_request.message)

        return ChatResponse(
            success=response.success,
            response=response.content,
            agent_type=chat_request.agent_type,
            capabilities=agent.get_capabilities(),
            metadata=response.metadata,
            error=response.error,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in chat endpoint")
        return ChatResponse(
            success=False,
            response="",
            agent_type=chat_request.agent_type,
            capabilities=[],
            error=str(exc),
        )


@api_router.post("/search", response_model=SearchResponse)
async def search_and_summarize(search_request: SearchRequest, request: Request):
    try:
        search_agent = await _get_or_create_agent(request, "search")
        search_prompt = (
            f"Search for information about: {search_request.query}. "
            "Provide a comprehensive summary with key findings."
        )
        result = await search_agent.execute(search_prompt, use_tools=True)

        if result.success:
            metadata = result.metadata or {}
            return SearchResponse(
                success=True,
                query=search_request.query,
                summary=result.content,
                search_results=metadata,
                sources_count=int(metadata.get("tool_run_count", metadata.get("tools_used", 0)) or 0),
            )

        return SearchResponse(
            success=False,
            query=search_request.query,
            summary="",
            sources_count=0,
            error=result.error,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in search endpoint")
        return SearchResponse(
            success=False,
            query=search_request.query,
            summary="",
            sources_count=0,
            error=str(exc),
        )


@api_router.get("/agents/capabilities")
async def get_agent_capabilities(request: Request):
    try:
        search_agent = await _get_or_create_agent(request, "search")
        chat_agent = await _get_or_create_agent(request, "chat")

        return {
            "success": True,
            "capabilities": {
                "search_agent": search_agent.get_capabilities(),
                "chat_agent": chat_agent.get_capabilities(),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error getting capabilities")
        return {"success": False, "error": str(exc)}


async def _generate_summary(content: str, request: Request) -> str:
    """Generate AI summary for article content."""
    try:
        chat_agent = await _get_or_create_agent(request, "chat")
        prompt = f"Summarize the following article in 2-3 concise sentences:\n\n{content[:2000]}"
        result = await chat_agent.execute(prompt)
        if result.success:
            return result.content
        return "Summary generation failed."
    except Exception as exc:
        logger.exception("Error generating summary")
        return "Summary not available."


@api_router.post("/articles", response_model=Article)
async def create_article(article_input: ArticleCreate, request: Request):
    db = _ensure_db(request)

    # Generate AI summary
    summary = await _generate_summary(article_input.content, request)

    article = Article(
        **article_input.model_dump(),
        summary=summary
    )

    await db.articles.insert_one(article.model_dump())
    return article


@api_router.get("/articles", response_model=List[Article])
async def get_articles(
    request: Request,
    category: Optional[str] = None,
    published: Optional[bool] = None,
    limit: int = 50
):
    db = _ensure_db(request)

    query = {}
    if category:
        query["category"] = category
    if published is not None:
        query["published"] = published

    articles = await db.articles.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    return [Article(**article) for article in articles]


@api_router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str, request: Request):
    db = _ensure_db(request)

    article = await db.articles.find_one({"id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count
    await db.articles.update_one(
        {"id": article_id},
        {"$inc": {"views": 1}}
    )
    article["views"] = article.get("views", 0) + 1

    return Article(**article)


@api_router.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: str, article_update: ArticleUpdate, request: Request):
    db = _ensure_db(request)

    article = await db.articles.find_one({"id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    update_data = {k: v for k, v in article_update.model_dump().items() if v is not None}

    # Regenerate summary if content changed
    if "content" in update_data:
        update_data["summary"] = await _generate_summary(update_data["content"], request)

    update_data["updated_at"] = datetime.now(timezone.utc)

    await db.articles.update_one({"id": article_id}, {"$set": update_data})

    updated_article = await db.articles.find_one({"id": article_id})
    return Article(**updated_article)


@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, request: Request):
    db = _ensure_db(request)

    result = await db.articles.delete_one({"id": article_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")

    return {"success": True, "message": "Article deleted"}


@api_router.post("/articles/{article_id}/share")
async def track_share(article_id: str, request: Request):
    db = _ensure_db(request)

    result = await db.articles.update_one(
        {"id": article_id},
        {"$inc": {"shares": 1}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")

    return {"success": True, "message": "Share tracked"}


@api_router.get("/categories", response_model=List[Category])
async def get_categories(request: Request):
    db = _ensure_db(request)
    categories = await db.categories.find().sort("name", 1).to_list(100)
    return [Category(**category) for category in categories]


@api_router.post("/categories", response_model=Category)
async def create_category(category_input: CategoryCreate, request: Request):
    db = _ensure_db(request)

    # Generate slug from name
    slug = category_input.name.lower().replace(" ", "-").replace("_", "-")

    # Check if slug already exists
    existing = await db.categories.find_one({"slug": slug})
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    category = Category(
        **category_input.model_dump(),
        slug=slug
    )

    await db.categories.insert_one(category.model_dump())
    return category


@api_router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image and return base64 encoded data."""
    try:
        # Read file content
        contents = await file.read()

        # Validate file size (max 5MB)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed")

        # Encode to base64
        base64_encoded = base64.b64encode(contents).decode('utf-8')

        # Create data URI
        image_data = f"data:{file.content_type};base64,{base64_encoded}"

        return {
            "success": True,
            "image_data": image_data,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(contents)
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error uploading image")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(exc)}")


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
