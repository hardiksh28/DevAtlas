from fastapi import APIRouter, Depends
from pydantic import BaseModel

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
    gateway: LLMGateway = Depends(get_llm_gateway),
) -> GenerateResponse:
    """Manual dev/debug endpoint for exercising the gateway directly over
    HTTP (e.g. confirming Ollama is reachable and the model is pulled).
    Feature modules should call get_llm_gateway() in-process instead —
    this route is for local verification only, not internal traffic.
    """
    result = await gateway.generate(body.operation, body.prompt)
    return GenerateResponse(response=result)
