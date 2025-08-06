import time
from workers import handler, fetch, Response
import os, json
import urllib.request as urlreq
from urllib.error import HTTPError, URLError
import ssl
import traceback
from pyodide.ffi import create_once_callable, to_js
import asyncio
from js import Promise
from repositories import ItineraryRepository
from utils import GCPAuthHelper, URLHelper
from pathlib import Path
from prompts import get_itineraries_prompt


class ItineraryService:

    def __init__(self, env, ctx):
        self.itinerary_repository = ItineraryRepository()
        self.gcp_auth_helper = GCPAuthHelper()
        self.env = env
        self.ctx = ctx

    async def create_itinerary(
        self,
        destination: str,
        duration_days: int,
        id_token: str,
        project_id: str,
        collection: str,
        llm_api_key: str,
    ):
        """
        Create an itinerary document in Firestore.
        """
        params = {
            "fields": {
                "destination": {"stringValue": destination},
                "durationDays": {"integerValue": duration_days},
                "status": {"stringValue": "processing"},
                "createdAt": {
                    "timestampValue": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                },
            }
        }
        document_id = await self.itinerary_repository.insert_document(
            id_token, project_id, collection, params
        )
        self.ctx.passThroughOnException()
        process_params = {
            "destination": destination,
            "durationDays": duration_days,
        }
        self.ctx.waitUntil(
            self.python_coroutine_to_js_promise(
                self.process_job(
                    document_id,
                    id_token,
                    project_id,
                    collection,
                    llm_api_key,
                    process_params,
                )
            )
        )
        if not document_id:
            raise Exception("Failed to create itinerary document")

        return document_id

    async def process_job(
        self,
        job_id: str,
        id_token: str,
        project_id: str,
        collection: str,
        llm_api_key: str,
        params: dict,
    ):
        """
        with 3 retry chat complete and update document with result itineraries, updated timestamp, retry count. if failed, update with error message in error field.
        params contains destination and durationDays.
        job_id is the document id in Firestore.
        """
        itinerary_repository = ItineraryRepository()
        print("process_job start")
        base_prompt = get_itineraries_prompt()
        prompt = base_prompt.replace("{{destination}}", params["destination"]).replace(
            "{{duration}}", str(params["durationDays"])
        )
        for i in range(3):
            try:
                print(f"Attempt {i + 1} to generate itinerary")
                response = await self.chat_completion(
                    prompt, llm_api_key, model="gpt-4o", temperature=0.7, max_tokens=500
                )
                if (
                    not response
                    or "choices" not in response
                    or len(response["choices"]) == 0
                ):
                    print(f"Invalid response from LLM: {response}")
                    raise ValueError("No valid response from LLM")

                itineraries = response["choices"][0]["message"]["content"]
                print("Itineraries generated successfully:", itineraries)
                itineraries = json.dumps(
                    json.loads(itineraries.replace("json", "").replace("```", ""))
                )
                updates = {
                    "itineraries": {"stringValue": itineraries},
                    "status": {"stringValue": "completed"},
                    "updatedAt": {
                        "timestampValue": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                        )
                    },
                    "completedAt": {
                        "timestampValue": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                        )
                    },
                    "retry_count": {"integerValue": i},
                }
                await itinerary_repository.update_document(
                    id_token, project_id, collection, job_id, updates
                )
                print("Document updated successfully")
                return
            except Exception as e:
                print(f"Error on attempt {i + 1}: {traceback.format_exc()}")
                updates = {
                    "updatedAt": {
                        "timestampValue": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                        )
                    },
                    "retry_count": {"integerValue": i},
                }
                backoff_time = 2**i
                await itinerary_repository.update_document(
                    id_token, project_id, collection, job_id, updates
                )
                print(f"Waiting for {backoff_time} seconds before retrying...")
                await asyncio.sleep(backoff_time)
        updates = {
            "updatedAt": {
                "timestampValue": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            "status": {"stringValue": "failed"},
            "error": {"stringValue": "3 retry exceed and failed"},
            "completedAt": {
                "timestampValue": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
        }
        await itinerary_repository.update_document(
            id_token, project_id, collection, job_id, updates
        )
        print("Document request failed after 3 retries, updated with error")

    async def chat_completion(
        self,
        prompt: str,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload).encode("utf‑8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            # add a custom UA if needed — OpenAI doesn't enforce one
        }

        resp = await fetch(
            url,
            method="POST",
            headers=headers,
            body=data,
        )
        if resp.status != 200:
            print("chat_completion Error:", resp.json())
            return None

        identity_response = await resp.json()

        return identity_response

    def python_coroutine_to_js_promise(self, coro):
        """Convert Python coroutine to JavaScript Promise"""

        async def wrapper():
            try:
                result = await coro
                return result
            except Exception as e:
                print(f"💥 [WRAPPER] Error in background task: {e}")
                raise e

        # Create a JavaScript Promise that resolves the Python coroutine
        return Promise.new(
            lambda resolve, reject: asyncio.create_task(wrapper()).add_done_callback(
                lambda task: (
                    resolve(None)
                    if task.exception() is None
                    else reject(task.exception())
                )
            )
        )
