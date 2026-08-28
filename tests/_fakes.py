"""Shared test doubles for the Discovery RAG pipeline (scoring/discovery/solution_shaping agents).

Import this BEFORE the agent modules — it sets ANTHROPIC_API_KEY so `anthropic.Anthropic()`
(constructed at agent import time) doesn't raise SystemExit.
"""
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-dummy-key")

import httpx
import anthropic

_DUMMY_REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


class FakeContentBlock:
    def __init__(self, text):
        self.text = text


class FakeMessage:
    """Stands in for the anthropic.types.Message returned by client.messages.create()."""

    def __init__(self, text):
        self.content = [FakeContentBlock(text)]


def make_authentication_error(message="Invalid API key"):
    return anthropic.AuthenticationError(message, response=httpx.Response(401, request=_DUMMY_REQUEST), body=None)


def make_bad_request_error(message="bad request"):
    return anthropic.BadRequestError(message, response=httpx.Response(400, request=_DUMMY_REQUEST), body=None)
