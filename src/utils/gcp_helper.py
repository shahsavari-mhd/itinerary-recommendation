from workers import handler, fetch, Response
import json
import traceback

class GCPAuthHelper:
    async def sign_in_with_password(self, email, password, api_key):
        """
        Sign in a user with email and password. get firebase api.
        return idToken value to use in other requests.
        """
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

        payload = {"email": email, "password": password, "returnSecureToken": True}
        data = json.dumps(payload).encode("utf-8")

        try:
            resp = await fetch(
                url,
                method="POST",
                headers={"Content-Type": "application/json"},
                body=data,
            )
            if resp.status != 200:
                print("sign_in_with_password Error:", resp.body)
                return None

            identity_response = await resp.json()
            print("Identity Response:", identity_response)
            id_token = identity_response.get("idToken")
            if not id_token:
                raise ValueError("ID Token not found in response")

            return id_token
        except Exception as e:
            print("sign_in_with_password Error:", traceback.format_exc())
            raise