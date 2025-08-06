import json
import traceback
from workers import handler, fetch, Response


class ItineraryRepository:
    
    async def insert_document(self, id_token, project_id, collection, document):
        """
        Insert a document into Firestore using the provided ID token.
        """
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection}"

        headers = {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }

        data = json.dumps(document, ensure_ascii=True).encode("utf-8")

        try:
            resp = await fetch(
                url,
                method="POST",
                headers=headers,
                body=data,
            )
            if resp.status != 200:
                print("insert_document Error:", json.dumps(await resp.json()))
                return None

            identity_response = await resp.json()
            print("Identity Response:", identity_response)
            name = identity_response.get("name")
            if not name:
                raise ValueError("Document ID not found in response")
            doc_id = name.split("/")[-1]  # Extract the document ID from the name

            return doc_id
        except Exception as e:
            print("insert_document Error:", traceback.format_exc())
            raise
            # return {"error": str(e)}


    async def update_document(self, id_token, project_id, collection, document_id, fields):
        """
        Update a document in Firestore using the provided ID token.
        The updates should be a dictionary with field names as keys and their new values.
        """
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection}/{document_id}"

        headers = {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }

        data = json.dumps({"fields": fields}).encode("utf-8")
        field_paths = list(fields.keys())
        update_mask = "&".join([f"updateMask.fieldPaths={field}" for field in field_paths])
        
        url_with_mask = f"{url}?{update_mask}"
        
        try:
            resp = await fetch(
                url_with_mask,
                method="PATCH",
                headers=headers,
                body=data,
            )
            if resp.status != 200:
                print("update_document Error:", await resp.json())
                print(
                    f"update_document parameters: \nupdates: {fields}\nurl: {url}\nheaders: {headers}"
                )
                return None

            identity_response = await resp.json()

            return identity_response
        except Exception as e:
            print("update_document URLError:", traceback.format_exc())
            return {"error": str(e)}


    async def get_document(self, id_token, project_id, collection, document_id):
        """
        Retrieve a document from Firestore using the provided ID token.
        """
        url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection}/{document_id}"

        headers = {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }

        try:
            resp = await fetch(
                url,
                method="GET",
                headers=headers,
            )
            if resp.status != 200:
                print("get_document Error:", resp.body)
                return None

            itinerary_response = await resp.json()

            return itinerary_response
        except Exception as e:
            print("get_document URLError:", traceback.format_exc())
            return {"error": str(e)}