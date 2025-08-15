from django.contrib.auth import get_user_model
import os
import requests


class NotConnectedToSocialException(Exception):
    pass


# TODO: add caching for this function per user, so that database lookups are low in numbers
def get_social_user(user, provider="linkedin"):
    try:
        linkedin_user = user.socialaccount_set.get(provider=provider)
    except Exception as e:
        raise NotConnectedToSocialException("User has not linked any provider") from e

    return linkedin_user


def get_share_headers(linkedin_user):
    token = linkedin_user.socialtoken_set.all()
    if not token.exists():
        raise ValueError("could not get the user token")

    social_token = token.first()
    return {
        "Authorization": f"Bearer {social_token.token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def get_user_id(linkedin_user):
    try:
        user_id = linkedin_user.uid
    except Exception as e:
        raise ValueError("Linkedin user id not found") from e

    return user_id


def share_linkedin(user, text: str):
    User = get_user_model()

    if not isinstance(user, User):
        raise ValueError("User is not a type of user")

    linkedin_user = get_social_user(user, "linkedin")

    header = get_share_headers(linkedin_user)
    user_id = get_user_id(linkedin_user)
    endpoint = os.getenv("LINKEDIN_API_ENDPOINT")

    payload = {
        "author": f"urn:li:person:{user_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    response = requests.post(endpoint, headers=header, json=payload, timeout=15)
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"There was an error while sharing on linkedin: {e}") from e
    return response
