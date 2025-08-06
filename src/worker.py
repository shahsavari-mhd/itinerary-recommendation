import time
from workers import handler, fetch, Response
import os, json
import traceback
from repositories import ItineraryRepository
from utils import GCPAuthHelper, URLHelper
from services import ItineraryService

async def on_fetch(request, env, ctx):
    FIREBASE_EMAIL = env.FIREBASE_EMAIL
    FIREBASE_PASSWORD = env.FIREBASE_PASSWORD
    FIREBASE_API_KEY = env.FIREBASE_API_KEY
    gcp_auth_helper=GCPAuthHelper()

    try:
        
        url = request.url
        method = request.method
        path = URLHelper(url).pathname
        print(f"on_fetch: {method} {path}")
        if not ((path == "/itinerary" and method == "GET") or (path == "/create" and method == "POST")):
            return Response(
                json.dumps({"error": f"Invalid endpoint"}),
                status=404,
                headers={"Content-Type": "application/json"},
            )
        id_token = await gcp_auth_helper.sign_in_with_password(
            FIREBASE_EMAIL, FIREBASE_PASSWORD, FIREBASE_API_KEY
        )
        if not id_token:
            return Response(
                json.dumps({"error": f"Failed to authenticate"}),
                status=401,
                headers={"Content-Type": "application/json"},
            )
        if path == "/itinerary" and method == "GET":
            return await get_itinerary(request, env, id_token)
        elif path == "/create" and method == "POST":
            return await create_itinerary(request, env, ctx, id_token)

    except Exception as e:
        print("on_fetch Error:", traceback.format_exc())
        return Response(
            json.dumps({"error": f"Internal server error"}),
            status=500,
                headers={"Content-Type": "application/json"},
        )


async def get_itinerary(request, env, id_token):
    """
    Handle GET request to retrieve an itinerary by job_id.
    """
    try:
        FIREBASE_PROJECT_ID = env.FIREBASE_PROJECT_ID
        FIRESTORE_COLLECTION = env.FIRESTORE_COLLECTION
        itinerary_repository = ItineraryRepository()
        search_params=URLHelper(request.url).searchParams
        if 'id' not in search_params:
            return Response(
                json.dumps({"error": "id is required"}),
                status=400,
                headers={"Content-Type": "application/json"},
            )
        id = search_params.get("id")
        if not id:
            return Response(
                json.dumps({"error": "id is required"}),
                headers={"Content-Type": "application/json"},
                status=400,
            )

        document = await itinerary_repository.get_document(
            id_token, FIREBASE_PROJECT_ID, FIRESTORE_COLLECTION, id
        )
        if not document:
            return Response(
                json.dumps({
                    "success": 'false',
                    "status": "not_found",
                    "message": "Itinerary not found"
                }),
                status=404,
                headers={"Content-Type": "application/json"},
            )
        status = document.get('fields', {}).get('status', {}).get('stringValue', '')
        if status=='processing':
            return Response(
                json.dumps({
                    "success": 'false',
                    "status": "generating",
                    "message": "Itinerary is still being generated"
                }),
                status=202,
                headers={"Content-Type": "application/json"},
            )
        elif status=='completed':
            return Response(
                json.dumps({
            "success": 'true',
            "status": "completed",
            "data": {
                "destination": document['fields']['destination']['stringValue'],
                "duration_days": document['fields']['durationDays']['integerValue'],
                "itinerary": document['fields']['itineraries']['stringValue']
            }
            }),
                status=202,
                headers={"Content-Type": "application/json"},
            )
        elif status=='failed':
            return Response(
                json.dumps({
                    "success": 'false',
                    "status": "failed",
                    "message": f"Itinerary generation failed. {document['fields']['error']['stringValue'] if 'error' in document['fields'] else 'Unknown error'}"
                }),
                status=202,
                headers={"Content-Type": "application/json"},
            )

        return Response(
            json.dumps({"error": "Internal server error"}),
            status=500,
                headers={"Content-Type": "application/json"},
        )
        
    except Exception as e:
        print("get_itinerary Error:", traceback.format_exc())
        return Response(
            json.dumps({"error": f"Internal server error"}),
            status=500,
                headers={"Content-Type": "application/json"},
        )


async def create_itinerary(request, env, ctx, id_token):
    try:
        FIREBASE_PROJECT_ID = env.FIREBASE_PROJECT_ID
        FIRESTORE_COLLECTION = env.FIRESTORE_COLLECTION
        LLM_API_KEY = env.LLM_API_KEY
        itinerary_service = ItineraryService(env, ctx)

        request_data = await request.json()
        if hasattr(request_data, 'to_py'):
            request_data = request_data.to_py()
            
        if not request_data or 'destination' not in request_data or 'durationDays' not in request_data:
            return Response(
                json.dumps({"error": "Invalid input: 'destination' and 'durationDays' are required"}),
                status=400,
                headers={"Content-Type": "application/json"},
            )
        destination = request_data['destination']
        duration_days = request_data['durationDays']

        document_id = await itinerary_service.create_itinerary(
            destination, duration_days, id_token, FIREBASE_PROJECT_ID, FIRESTORE_COLLECTION, LLM_API_KEY
        )

        return Response(
            json.dumps({"success": 'true',
  "id": document_id,
  "message": "Itinerary generation started"
                }), status=202, headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        print("on_fetch Error:", traceback.format_exc())
        return Response(
            json.dumps({"error": "Internal server error"}),
            status=500,
            headers={"Content-Type": "application/json"},
        )
