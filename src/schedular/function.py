""" This file contains the functions for the schedular."""

from datetime import timedelta, datetime
from django.utils import timezone
from django.db import models
import inngest
import requests

from posts.models import Post
from .client import inngest_client


def get_now():
    """Get the current time in the timezone of the user."""
    return timezone.now().astimezone().timestamp()


def workflow_share_on_linkedin_node(instance: models.Model) -> tuple[bool, str]:
    """Share the post on Linkedin."""
    try:
        instance.validate_can_share_on_socials()
    except requests.exceptions.RequestException as e:
        print(f"error {e}")
        return (
            False,
            f"Problem saving instance, stopping sharing: {e}",
        )

    instance = instance.perform_share_on_social(mock=True, save=False)
    return True, "shared on Linkedin"


@inngest_client.create_function(
    fn_id="post_schedular",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="post/post.scheduled"),
)
def post_schedular(ctx: inngest.Context) -> tuple[str, str | Exception]:
    """Schedule the post on Linkedin."""
    try:
        ctx.logger.info(ctx.event.data)

        object_id = ctx.event.data.get("object_id")

        # pylint: disable=no-member
        qs = Post.objects.filter(id=object_id)
        if not qs.exists():
            return "missing", f"Post not found for object_id: {object_id}"
        instance = qs.first()

        start_at = ctx.step.run("workflow_start", get_now)
        start_at = datetime.fromtimestamp(start_at)
        qs.update(share_start_at=start_at)
        share_platforms = instance.scheduled_platform()

        if "linkedin" in share_platforms:
            # handle linkedin
            # publish_date = instance.share_at + timedelta(seconds=7)
            # if instance.share_at:
            #     publish_date = instance.share_at + timedelta(seconds=7)

            ctx.step.sleep_until(
                "linkedin_sleep_schedular", timezone.now() + timedelta(seconds=3)
            )
            did_share, share_message = ctx.step.run(
                "linkedin-share-workflow-step",
                lambda: workflow_share_on_linkedin_node(instance),
            )
            if did_share:
                ctx.logger.info(f"shared function for Object_id: {object_id} worked")
            else:
                ctx.logger.info(share_message)

        end_at = ctx.step.run("workflow_start", get_now)
        end_at = datetime.fromtimestamp(end_at)
        qs.update(share_completed_at=timezone.now())

        return "done"
    # pylint: disable=broad-exception-caught
    except Exception as error:
        print(f"something went wrong {error}")
        return "something went wrong", error
