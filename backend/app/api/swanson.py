"""Swanson AI recommendation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.checkin import Checkin
from app.models.content import Content
from app.models.user import User
from app.schemas.swanson import RecommendRequest, RecommendResponse
from app.services.llm import get_llm


router = APIRouter(prefix="/swanson", tags=["swanson"])


SYSTEM_PROMPT = """You are Swanson, a straightforward TV and movie recommendation assistant.

Your job is to help users find something to watch based on their viewing history and preferences.

Guidelines:
- Be direct and practical - no fluff
- Give 2-3 specific recommendations with brief explanations
- Focus on WHY each recommendation fits the user's taste
- If the search results are provided, prioritize those but feel free to suggest others
- If the user hasn't watched much, acknowledge that and give broader suggestions
- Keep responses concise - around 100-150 words max

User's viewing history and preferences will be provided as context.
"""


async def get_user_taste_profile(db: AsyncSession, user_id: int) -> dict:
    """Build a taste profile from user's checkin history.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Dict with genre counts, recent watches, and viewing patterns
    """
    # Get recent checkins with content info
    result = await db.execute(
        select(Checkin)
        .where(Checkin.user_id == user_id)
        .options(
            selectinload(Checkin.content).selectinload(Content.genres)
        )
        .order_by(Checkin.watched_at.desc())
        .limit(50)
    )
    checkins = result.scalars().all()

    if not checkins:
        return {
            "total_watches": 0,
            "genres": {},
            "recent_titles": [],
            "content_types": {},
        }

    # Aggregate data
    genre_counts: dict[str, int] = {}
    content_type_counts: dict[str, int] = {}
    recent_titles: list[str] = []

    for checkin in checkins:
        content = checkin.content
        if not content:
            continue

        # Count content types
        content_type_counts[content.content_type] = (
            content_type_counts.get(content.content_type, 0) + 1
        )

        # Track recent titles (first 10)
        if len(recent_titles) < 10:
            recent_titles.append(content.name)

        # Count genres
        for genre in content.genres:
            genre_counts[genre.name] = genre_counts.get(genre.name, 0) + 1

    # Sort genres by count
    sorted_genres = dict(
        sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    )

    return {
        "total_watches": len(checkins),
        "genres": sorted_genres,
        "recent_titles": recent_titles,
        "content_types": content_type_counts,
    }


def build_user_prompt(
    user_prompt: str,
    taste_profile: dict,
    search_results: list[dict],
) -> str:
    """Build the full user prompt with context.

    Args:
        user_prompt: User's question/request
        taste_profile: User's taste profile from checkins
        search_results: Current search results

    Returns:
        Formatted prompt string
    """
    parts = []

    # Add taste profile
    if taste_profile["total_watches"] > 0:
        parts.append("## User's Viewing Profile")
        parts.append(f"Total watches logged: {taste_profile['total_watches']}")

        if taste_profile["genres"]:
            top_genres = list(taste_profile["genres"].keys())[:5]
            parts.append(f"Top genres: {', '.join(top_genres)}")

        if taste_profile["recent_titles"]:
            parts.append(f"Recently watched: {', '.join(taste_profile['recent_titles'][:5])}")

        if taste_profile["content_types"]:
            types = [
                f"{k}s ({v})" for k, v in taste_profile["content_types"].items()
            ]
            parts.append(f"Content types: {', '.join(types)}")
    else:
        parts.append("## User's Viewing Profile")
        parts.append("No viewing history available yet.")

    # Add search results if present
    if search_results:
        parts.append("\n## Current Search Results")
        parts.append("The user is looking at these options:")
        for item in search_results[:10]:
            genres_str = f" ({', '.join(item.get('genres', []))})" if item.get("genres") else ""
            year_str = f" ({item.get('year')})" if item.get("year") else ""
            parts.append(f"- {item['name']}{year_str}{genres_str} [{item['type']}]")

    # Add user's question
    parts.append(f"\n## User's Question\n{user_prompt}")

    return "\n".join(parts)


@router.post("/recommend", response_model=RecommendResponse)
async def get_recommendation(
    request: RecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get an AI-powered recommendation based on user's history and search context.

    Args:
        request: Recommendation request with prompt and optional search results
        current_user: Authenticated user
        db: Database session

    Returns:
        AI-generated recommendation
    """
    try:
        # Get user's taste profile from checkins
        taste_profile = await get_user_taste_profile(db, current_user.id)

        # Build the full prompt
        user_prompt = build_user_prompt(
            request.prompt,
            taste_profile,
            [r.model_dump() for r in request.search_results],
        )

        # Get LLM and generate recommendation
        llm = get_llm()
        recommendation = await llm.complete(SYSTEM_PROMPT, user_prompt)

        return RecommendResponse(
            recommendation=recommendation,
            cached=False,
        )

    except ValueError as e:
        # LLM not configured
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendation: {str(e)}",
        )


@router.post("/recommend/stream")
async def get_recommendation_stream(
    request: RecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream an AI-powered recommendation.

    Returns Server-Sent Events with text chunks as they're generated.
    """
    try:
        # Get user's taste profile from checkins
        taste_profile = await get_user_taste_profile(db, current_user.id)

        # Build the full prompt
        user_prompt = build_user_prompt(
            request.prompt,
            taste_profile,
            [r.model_dump() for r in request.search_results],
        )

        # Get LLM
        llm = get_llm()

        async def generate():
            try:
                async for chunk in llm.stream(SYSTEM_PROMPT, user_prompt):
                    # SSE format: data: <content>\n\n
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: [ERROR] {str(e)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
