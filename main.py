from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import ollama

from typing import Optional, Dict, List

import uuid
import re

from fact_extract import fact_extractor
from refdatabase import wikipedia_verifier
from confidence_scorer import confidence_scorer
from contradiction_detector import contradiction_detector


app = FastAPI(
    title="LLM Hallucination Prevention API"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MODEL_NAME = "qwen3:4b"


SYSTEM_PROMPT = """
You are a concise factual assistant.

Answer the user's question directly and clearly.

Rules:
- Answer in 1 to 3 sentences.
- Do not use Markdown.
- Do not use headings, bullet points, tables, or emojis.
- Do not add unnecessary historical background.
- Do not mention Wikipedia or other sources.
- Do not invent citations.
- State factual claims clearly and precisely.
- If the question asks for one fact, give that fact directly.
- If you are uncertain, say that you are uncertain instead of inventing information.
"""


conversations = {}


class ChatRequest(BaseModel):

    message: str

    session_id: Optional[str] = None


class ChatResponse(BaseModel):

    answer: str

    session_id: str

    provider: str

    model: str

    status: str

    confidence: str

    summary: str

    claims: List[Dict]


@app.get("/")
async def root():

    return {
        "status": (
            "LLM Hallucination Prevention API "
            "is running"
        ),
        "provider": "ollama",
        "model": MODEL_NAME
    }


@app.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest
):

    try:

        # ==========================================
        # SESSION
        # ==========================================

        session_id = (
            request.session_id
            or str(uuid.uuid4())
        )

        if session_id not in conversations:

            conversations[
                session_id
            ] = []

        history = conversations[
            session_id
        ]

        # ==========================================
        # OLLAMA
        # ==========================================

        ollama_messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        for message in history:

            ollama_messages.append({
                "role": message["role"],
                "content": message["content"]
            })

        ollama_messages.append({
            "role": "user",
            "content": request.message
        })

        response = ollama.chat(
            model=MODEL_NAME,
            messages=ollama_messages
        )

        response_text = (
            response[
                "message"
            ][
                "content"
            ]
            .strip()
        )

        # ==========================================
        # CLEAN LLM RESPONSE
        # ==========================================

        response_text = re.sub(
            r"\*\*(.*?)\*\*",
            r"\1",
            response_text
        )

        response_text = re.sub(
            r"\*(.*?)\*",
            r"\1",
            response_text
        )

        response_text = re.sub(
            r"^#{1,6}\s*",
            "",
            response_text,
            flags=re.MULTILINE
        )

        response_text = re.sub(
            r"^\s*[-•]\s*",
            "",
            response_text,
            flags=re.MULTILINE
        )

        response_text = re.sub(
            r"\n{2,}",
            "\n",
            response_text
        )

        response_text = response_text.strip()

        # ==========================================
        # SAVE CONVERSATION
        # ==========================================

        conversations[
            session_id
        ].append({
            "role": "user",
            "content": request.message
        })

        conversations[
            session_id
        ].append({
            "role": "assistant",
            "content": response_text
        })

        # ==========================================
        # FACT EXTRACTION
        # ==========================================

        extracted_facts = (
            fact_extractor.extract_facts(
                response_text
            )
        )

        # ==========================================
        # WIKIPEDIA VERIFICATION
        # ==========================================

        verified_facts = (
            wikipedia_verifier.verify_facts(
                extracted_facts
            )
        )

        # ==========================================
        # CONTRADICTION DETECTION
        # ==========================================

        contradictions = (
            contradiction_detector.detect_contradictions(
                session_id,
                verified_facts
            )
        )

        contradiction_detector.add_facts(
            session_id,
            verified_facts
        )

        # ==========================================
        # CONFIDENCE
        # ==========================================

        confidence_report = (
            confidence_scorer.score_response(
                verified_facts
            )
        )

        confidence = (
            confidence_report.get(
                "overall_confidence",
                "unknown"
            )
        )

        # ==========================================
        # CLAIMS
        # ==========================================

        claims = []

        for fact in verified_facts:

            claim_status = "unverified"

            claim_confidence = (
                fact.get(
                    "confidence",
                    "unknown"
                )
            )

            if fact.get("verified"):

                if claim_confidence == "high":

                    claim_status = "verified"

                elif claim_confidence == "medium":

                    claim_status = (
                        "partially_verified"
                    )

                else:

                    claim_status = "verified"

            # --------------------------------------
            # CONTRADICTION
            # --------------------------------------

            for contradiction in contradictions:

                current_value = (
                    contradiction.get(
                        "current_value",
                        ""
                    )
                )

                fact_value = (
                    fact.get(
                        "value",
                        fact.get(
                            "entity",
                            ""
                        )
                    )
                )

                if (
                    current_value
                    and fact_value
                    and current_value.lower()
                    == fact_value.lower()
                ):

                    claim_status = (
                        "contradicted"
                    )

                    claim_confidence = "low"

                    break

            # --------------------------------------
            # CLAIM DATA
            # --------------------------------------

            claim_data = {

                "claim": fact.get(
                    "claim",
                    fact.get(
                        "sentence",
                        ""
                    )
                ),

                "subject": fact.get(
                    "subject"
                ),

                "relation": fact.get(
                    "relation"
                ),

                "value": fact.get(
                    "value",
                    fact.get(
                        "entity"
                    )
                ),

                "aliases": fact.get(
                    "aliases",
                    []
                ),

                "status": claim_status,

                "confidence": claim_confidence,

                "evidence": fact.get(
                    "evidence"
                ),

                "source": None
            }

            # --------------------------------------
            # SOURCE
            # --------------------------------------

            if (
                fact.get(
                    "wikipedia_title"
                )
                and fact.get(
                    "wikipedia_url"
                )
            ):

                claim_data[
                    "source"
                ] = {

                    "title": fact.get(
                        "wikipedia_title"
                    ),

                    "url": fact.get(
                        "wikipedia_url"
                    )
                }

            claims.append(
                claim_data
            )

        # ==========================================
        # OVERALL STATUS
        # ==========================================

        total_count = len(
            claims
        )

        verified_count = sum(
            1
            for claim in claims
            if claim["status"]
            == "verified"
        )

        contradicted_count = sum(
            1
            for claim in claims
            if claim["status"]
            == "contradicted"
        )

        # ------------------------------------------
        # CONTRADICTED
        # ------------------------------------------

        if contradicted_count > 0:

            status = "contradicted"

            confidence = "low"

            summary = (
                f"{contradicted_count} factual "
                "claim(s) were contradicted."
            )

        # ------------------------------------------
        # NO CLAIMS
        # ------------------------------------------

        elif total_count == 0:

            status = "unverified"

            confidence = "unknown"

            summary = (
                "No factual claims could "
                "be verified."
            )

        # ------------------------------------------
        # EVERYTHING VERIFIED
        # ------------------------------------------

        elif verified_count == total_count:

            status = "verified"

            confidence = "high"

            summary = (
                "All factual claims were "
                "successfully verified."
            )

        # ------------------------------------------
        # PARTIAL
        # ------------------------------------------

        elif verified_count > 0:

            status = (
                "partially_verified"
            )

            confidence = "medium"

            summary = (
                f"{verified_count} of "
                f"{total_count} factual claims "
                "were verified. Some information "
                "may require further checking."
            )

        # ------------------------------------------
        # NOTHING VERIFIED
        # ------------------------------------------

        else:

            status = "unverified"

            confidence = "low"

            summary = (
                "The factual claims in the "
                "answer could not be verified."
            )

        # ==========================================
        # RESPONSE
        # ==========================================

        return ChatResponse(

            answer=response_text,

            session_id=session_id,

            provider="ollama",

            model=MODEL_NAME,

            status=status,

            confidence=confidence,

            summary=summary,

            claims=claims
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==================================================
# HISTORY
# ==================================================

@app.get(
    "/history/{session_id}"
)
async def get_history(
    session_id: str
):

    if session_id not in conversations:

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return {
        "session_id": session_id,
        "history": conversations[
            session_id
        ]
    }


# ==================================================
# CLEAR SESSION
# ==================================================

@app.delete(
    "/session/{session_id}"
)
async def clear_session(
    session_id: str
):

    if session_id in conversations:

        del conversations[
            session_id
        ]

    contradiction_detector.clear_session(
        session_id
    )

    return {
        "message": (
            f"Session {session_id} cleared"
        )
    }