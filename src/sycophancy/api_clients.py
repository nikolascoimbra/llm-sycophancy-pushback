"""Direct-API clients for the prereg-v1 factorial.

We deliberately avoid Bedrock here for two reasons:

  1. Bedrock does NOT expose the Anthropic ``web_search_20260209`` tool, and
     the v1 factorial requires native first-party web search for the G=On
     condition.
  2. Bedrock + direct-API snapshots can differ; routing v1 entirely through
     direct APIs keeps the snapshot constant within the factorial.

Each ``call_<provider>`` function takes a list of OpenAI-style messages plus a
``grounding`` flag and returns a ``ProviderResponse`` with the fields the
caching layer needs: free-text content, prompt + completion token counts,
the number of tool invocations the model issued, the cost in USD, and the
raw provider response for the cache.

Coverage of the G factor:

  - anthropic_sonnet_46 : native web_search tool, server-side execution.
  - openai_gpt5       : Responses API with built-in ``web_search`` tool.
  - google_gemini     : ``google_search`` grounding via google-genai.
  - deepseek_v3_2     : NO native search; G=On is NOT supported and the call
                        raises ``GroundingUnsupportedError``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Literal

PROVIDERS = ("anthropic_sonnet_46", "openai_gpt5", "google_gemini", "deepseek_v3_2")

# Direct-API model IDs (snapshot 2026-05).
# Anthropic arm uses Sonnet 4.6 rather than Opus 4.7 because (1) Sonnet is the
# default model served to consumer claude.ai free-tier users — the population
# whose behavior we are trying to characterize; (2) Opus tools-on calls cost
# ~$0.05 each due to tool-spec input overhead (3000+ tokens × $15/M), which
# blows the $25 v1 budget; Sonnet input pricing is ~5x cheaper and fits in
# the cap with margin. Documented in docs/AMENDMENTS.md A6 and
# prereg/PRE_REGISTRATION_v1.md §2.
MODEL_IDS = {
    "anthropic_sonnet_46": "claude-sonnet-4-6",
    "openai_gpt5": "gpt-5",
    "google_gemini": "gemini-2.5-pro",
    "deepseek_v3_2": "deepseek-chat",  # DeepSeek-V3.2 served under deepseek-chat alias
}

# Pricing snapshot (USD per 1M tokens), 2026-05. Approximate.
PRICE = {
    "anthropic_sonnet_46": (3.00, 15.00),
    "openai_gpt5": (1.25, 10.00),
    "google_gemini": (1.25, 10.00),
    "deepseek_v3_2": (0.28, 1.10),
}

# Prompt-cache discount (Anthropic ephemeral cache): cache writes cost 25% more
# than base input, cache reads cost 10% of base. We approximate cost by base
# pricing and let actual billing settle — but enable cache_control on the
# tool spec block to dramatically reduce per-call cost on repeat calls.
ANTHROPIC_CACHE_TTL_SECONDS = 300

# Anthropic web_search per-search billing.
ANTHROPIC_WEB_SEARCH_PER_SEARCH = 0.01  # $10 / 1000 searches

Role = Literal["user", "assistant", "system"]


class GroundingUnsupportedError(RuntimeError):
    """Raised when a provider does not support native web-search grounding."""


@dataclass
class Message:
    role: Role
    content: str


@dataclass
class ProviderResponse:
    text: str
    input_tokens: int
    output_tokens: int
    tool_invocations: int  # number of search calls the model issued (0 if grounding off)
    usd: float
    raw: dict[str, Any] = field(default_factory=dict)


def _cost(provider: str, in_tok: int, out_tok: int, n_searches: int = 0) -> float:
    pin, pout = PRICE[provider]
    base = (in_tok * pin + out_tok * pout) / 1_000_000
    if provider == "anthropic_sonnet_46":
        base += n_searches * ANTHROPIC_WEB_SEARCH_PER_SEARCH
    return base


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

def call_anthropic_sonnet_46(
    messages: list[Message],
    *,
    grounding: bool,
    max_tokens: int = 800,
    client: Any = None,
) -> ProviderResponse:
    import anthropic

    if client is None:
        client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            # Use the SDK's built-in retry, which respects the retry-after
            # header. The SDK default of 2 retries is too low for sustained
            # rate-limit pressure; 8 attempts with the SDK's smart wait keeps
            # us well under the 50-RPM org limit without long blind backoff.
            max_retries=8,
        )

    def _do_call(**kw):
        return client.messages.create(**kw)

    kwargs: dict[str, Any] = {
        "model": MODEL_IDS["anthropic_sonnet_46"],
        "max_tokens": max_tokens,
        "messages": [{"role": m.role, "content": m.content} for m in messages
                      if m.role != "system"],
    }
    sys_msgs = [m.content for m in messages if m.role == "system"]
    if sys_msgs:
        kwargs["system"] = "\n\n".join(sys_msgs)
    if grounding:
        # Cache the tool definition block (~3k tokens of static spec) so repeat
        # calls within the cache TTL pay 10% of base input rate on it.
        kwargs["tools"] = [{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5,
            "cache_control": {"type": "ephemeral"},
        }]

    resp = _do_call(**kwargs)

    # Extract free-text content. With server-side web_search the response may
    # include tool_use + tool_result blocks; we only want assistant text.
    text_parts: list[str] = []
    n_tool_uses = 0
    for block in resp.content:
        btype = getattr(block, "type", None)
        if btype == "text":
            text_parts.append(getattr(block, "text", "") or "")
        elif btype == "server_tool_use":
            n_tool_uses += 1
        elif btype == "web_search_tool_result":
            # Server-side result, count not the tool use.
            pass
    text = "".join(text_parts).strip()

    usage = resp.usage
    in_tok = int(usage.input_tokens)
    out_tok = int(usage.output_tokens)
    cache_read = int(getattr(usage, "cache_read_input_tokens", 0) or 0)
    cache_write = int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
    # The Anthropic SDK reports input_tokens / cache_read / cache_write as
    # disjoint counts of separately-billed tokens. Sum them at their rates.
    pin, pout = PRICE["anthropic_sonnet_46"]
    input_cost = (in_tok * pin
                  + cache_read * pin * 0.10
                  + cache_write * pin * 1.25) / 1_000_000
    output_cost = out_tok * pout / 1_000_000
    usd = input_cost + output_cost + n_tool_uses * ANTHROPIC_WEB_SEARCH_PER_SEARCH
    return ProviderResponse(
        text=text, input_tokens=in_tok + cache_read + cache_write,
        output_tokens=out_tok,
        tool_invocations=n_tool_uses, usd=usd,
        raw=resp.model_dump(mode="json"),
    )


# ---------------------------------------------------------------------------
# OpenAI Responses API
# ---------------------------------------------------------------------------

def call_openai_gpt5(
    messages: list[Message],
    *,
    grounding: bool,
    max_tokens: int = 1500,
    client: Any = None,
) -> ProviderResponse:
    from openai import OpenAI

    if client is None:
        client = OpenAI()

    # Responses API takes a single ``input`` field which can be a list of
    # role/content pairs. We pass messages in OpenAI's expected shape.
    input_messages = [
        {"role": m.role, "content": m.content} for m in messages
    ]

    # GPT-5 reasoning effort is fixed at "low" across ALL cells (tools-off and
    # tools-on) to eliminate the grounding × reasoning-effort confound. The
    # earlier policy used "minimal" for tools-off + "low" for tools-on
    # (because the Responses API rejects effort="minimal" combined with the
    # web_search tool), which made the GPT-5 grounding contrast mix two
    # changes. Unifying on "low" everywhere isolates the grounding effect.
    # Documented in docs/AMENDMENTS.md A11.
    kwargs: dict[str, Any] = {
        "model": MODEL_IDS["openai_gpt5"],
        "input": input_messages,
        "max_output_tokens": max_tokens,
        "reasoning": {"effort": "low"},
    }
    if grounding:
        kwargs["tools"] = [{"type": "web_search"}]

    resp = client.responses.create(**kwargs)

    # The Responses API exposes a convenience ``output_text`` aggregating
    # message content; fall back to walking the items if absent.
    text = getattr(resp, "output_text", None) or ""
    if not text:
        parts = []
        for item in getattr(resp, "output", []) or []:
            if getattr(item, "type", None) == "message":
                for c in getattr(item, "content", []) or []:
                    t = getattr(c, "text", None)
                    if t:
                        parts.append(t)
        text = "".join(parts).strip()

    n_tool_uses = 0
    for item in getattr(resp, "output", []) or []:
        itype = getattr(item, "type", None)
        if itype and ("web_search" in itype or "tool_call" in itype):
            n_tool_uses += 1

    usage = resp.usage
    in_tok = int(getattr(usage, "input_tokens", 0) or 0)
    out_tok = int(getattr(usage, "output_tokens", 0) or 0)
    usd = _cost("openai_gpt5", in_tok, out_tok, n_searches=n_tool_uses)
    return ProviderResponse(
        text=text, input_tokens=in_tok, output_tokens=out_tok,
        tool_invocations=n_tool_uses, usd=usd,
        raw=resp.model_dump(mode="json") if hasattr(resp, "model_dump")
            else json.loads(resp.json()),
    )


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------

def call_google_gemini(
    messages: list[Message],
    *,
    grounding: bool,
    max_tokens: int = 800,
    client: Any = None,
) -> ProviderResponse:
    from google import genai
    from google.genai import errors as genai_errors
    from google.genai import types as gtypes
    from tenacity import (
        retry, retry_if_exception_type, stop_after_attempt, wait_exponential,
    )

    if client is None:
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    # Convert OpenAI-style messages to Gemini contents (role: user|model).
    contents: list[gtypes.Content] = []
    system_instruction = None
    for m in messages:
        if m.role == "system":
            system_instruction = m.content
            continue
        role = "model" if m.role == "assistant" else "user"
        contents.append(gtypes.Content(role=role, parts=[gtypes.Part(text=m.content)]))

    config_kwargs: dict[str, Any] = {
        "max_output_tokens": max_tokens,
        # Gemini 2.5 Pro requires thinking_budget ≥ 128 (Pro is a thinking-only
        # model; budget=0 returns 400). Setting the minimum keeps cost
        # predictable while still allowing a small reasoning step on hard
        # SimpleQA items. Empirically 128 yields ~70 thought tokens + ~10-30
        # response tokens for a verbalized-confidence answer.
        "thinking_config": gtypes.ThinkingConfig(thinking_budget=128),
    }
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    if grounding:
        config_kwargs["tools"] = [
            gtypes.Tool(google_search=gtypes.GoogleSearch()),
        ]

    @retry(
        retry=retry_if_exception_type(genai_errors.ClientError),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(6),
        reraise=True,
    )
    def _do_call():
        return client.models.generate_content(
            model=MODEL_IDS["google_gemini"],
            contents=contents,
            config=gtypes.GenerateContentConfig(**config_kwargs),
        )

    resp = _do_call()

    text = (resp.text or "").strip()

    # Tool-call count: grounding metadata reports if/how Google Search was used.
    n_tool_uses = 0
    cand = (resp.candidates or [None])[0]
    gm = getattr(cand, "grounding_metadata", None) if cand else None
    if gm is not None:
        queries = getattr(gm, "web_search_queries", None) or []
        n_tool_uses = len(queries)

    usage = resp.usage_metadata
    in_tok = int(getattr(usage, "prompt_token_count", 0) or 0)
    out_tok = int(getattr(usage, "candidates_token_count", 0) or 0)
    usd = _cost("google_gemini", in_tok, out_tok, n_searches=0)
    return ProviderResponse(
        text=text, input_tokens=in_tok, output_tokens=out_tok,
        tool_invocations=n_tool_uses, usd=usd,
        raw=resp.model_dump(mode="json") if hasattr(resp, "model_dump") else {},
    )


# ---------------------------------------------------------------------------
# DeepSeek (OpenAI-compatible)
# ---------------------------------------------------------------------------

def call_deepseek_v3_2(
    messages: list[Message],
    *,
    grounding: bool,
    max_tokens: int = 800,
    client: Any = None,
) -> ProviderResponse:
    if grounding:
        raise GroundingUnsupportedError(
            "DeepSeek V3.2 does not expose a first-party web_search tool; "
            "G=On cells are not run for this provider (see prereg-v1 §2.1)."
        )

    from openai import OpenAI

    if client is None:
        client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com/v1",
        )

    r = client.chat.completions.create(
        model=MODEL_IDS["deepseek_v3_2"],
        messages=[{"role": m.role, "content": m.content} for m in messages],
        max_tokens=max_tokens,
        temperature=0.0,
    )
    text = (r.choices[0].message.content or "").strip()
    in_tok = int(r.usage.prompt_tokens)
    out_tok = int(r.usage.completion_tokens)
    usd = _cost("deepseek_v3_2", in_tok, out_tok)
    return ProviderResponse(
        text=text, input_tokens=in_tok, output_tokens=out_tok,
        tool_invocations=0, usd=usd,
        raw=r.model_dump(mode="json"),
    )


CALLERS = {
    "anthropic_sonnet_46": call_anthropic_sonnet_46,
    "openai_gpt5": call_openai_gpt5,
    "google_gemini": call_google_gemini,
    "deepseek_v3_2": call_deepseek_v3_2,
}


def call(provider: str, messages: list[Message], *, grounding: bool,
         max_tokens: int | None = None) -> ProviderResponse:
    """Dispatch to the per-provider client."""
    fn = CALLERS[provider]
    kw: dict[str, Any] = {"grounding": grounding}
    if max_tokens is not None:
        kw["max_tokens"] = max_tokens
    return fn(messages, **kw)
