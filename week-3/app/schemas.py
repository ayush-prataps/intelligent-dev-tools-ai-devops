from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    model: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    model: Optional[str] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_duration: Optional[int] = None
    latency_ms: Optional[float] = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_title: str
    section: str
    similarity_score: float
    text: str


class RagRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    model: Optional[str] = None


class RagResponse(BaseModel):
    question: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    grounding_summary: str
    model: Optional[str] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_duration: Optional[int] = None
    latency_ms: Optional[float] = None


class CompareRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class CompareResponse(BaseModel):
    question: str
    direct_answer: str
    rag_answer: str
    retrieved_chunks: List[RetrievedChunk]


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class RetrieveResponse(BaseModel):
    query: str
    top_k: int
    retrieved_chunks: List[RetrievedChunk]


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: Optional[str] = None


class GenerateResponse(BaseModel):
    answer: str
    model: str


class TraceStep(BaseModel):
    step: int
    service: str
    action: str
    status: str
    elapsed_ms: float


class OrchestrateRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class OrchestrateResponse(BaseModel):
    question: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    orchestration_trace: List[TraceStep]
    total_elapsed_ms: float


class RAGEvaluationRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    models: List[str] = Field(default_factory=list)


class RAGEvaluationResponse(BaseModel):
    question: str
    retrieved_chunks: List[RetrievedChunk]
    results: List[Dict[str, Any]]


class GuardrailEvaluationRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    models: List[str] = Field(default_factory=list)


class GuardrailEvaluationResponse(BaseModel):
    question: str
    retrieved_chunks: List[RetrievedChunk]
    guardrail_threshold: float
    highest_similarity: float
    guardrail_passed: bool
    guardrail_triggered: bool
    guarded_result: Dict[str, Any]
    unguarded_results: List[Dict[str, Any]]


class DatasetEvaluationRequest(BaseModel):
    models: List[str] = Field(default_factory=list)
    limit: Optional[int] = Field(default=None, ge=1, le=100)


class DatasetEvaluationResponse(BaseModel):
    dataset: str
    models: List[str]
    question_count: int
    elapsed_ms: float
    resource_usage: Dict[str, Any]
    model_comparison: Dict[str, Any]
