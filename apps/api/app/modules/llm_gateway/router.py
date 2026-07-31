from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.llm_gateway.gateway import LLMGateway, get_llm_gateway

router = APIRouter(prefix="/v1/llm-gateway", tags=["LLM Orchestration Gateway"])


class GenerateRequest(BaseModel):
    operation: str = "debug"
    prompt: str


class GenerateResponse(BaseModel):
    response: str


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    gateway: LLMGateway = Depends(get_llm_gateway),
) -> GenerateResponse:
    """Manual dev/debug endpoint for exercising the gateway directly over
    HTTP (e.g. confirming Ollama is reachable and the model is pulled).
    Feature modules should call get_llm_gateway() in-process instead —
    this route is for authenticated local verification only, not internal
    traffic; it is not mounted at all in production (see main.py).
    """
    result = await gateway.generate(body.operation, body.prompt)
    return GenerateResponse(response=result)
