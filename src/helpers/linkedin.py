from django.contrib.auth import get_user_model
import requests


class NotConnectedToSocialException(Exception):
    pass


# TODO: add caching for this function per user, so that database lookups are low in numbers
def get_social_user(user, provider="linkedin"):
    try:
        linkedin_user = user.socialaccount_set.get(provider=provider)
    except Exception as e:
        raise NotConnectedToSocialException(
            "User has not linked any provider") from e

    return linkedin_user


def get_share_headers(linkedin_user):
    token = linkedin_user.socialtoken_set.all()
    if not token.exists():
        raise Exception("could not get the user token")

    social_token = token.first()
    return {
        "Authorization": f"Bearer {social_token.token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def get_user_id(linkedin_user):
    try:
        user_id = linkedin_user.uid
    except:
        raise Exception("Linkedin user id not found")

    return user_id


def share_linkedin(user, text: str):
    User = get_user_model()

    if not isinstance(user, User):
        raise Exception("User is not a type of user")

    linkedin_user = get_social_user(user, "linkedin")

    header = get_share_headers(linkedin_user)
    user_id = get_user_id(linkedin_user)
    endpoint = "https://api.linkedin.com/v2/ugcPosts"

    payload = {
        "author": f"urn:li:person:{user_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": "Hello World! This is my first Share on LinkedIn!"
                },
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    response = requests.post(endpoint, headers=header, json=payload)
    try:
        response.raise_for_status()
    except Exception as e:
        raise Exception(
            f"There was an error which i can't should coz of skill issues: {e}") from e
    return response
