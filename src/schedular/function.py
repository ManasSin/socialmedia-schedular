import inngest
from django.utils import timezone
from .client import inngest_client
from posts.models import Post
from datetime import timedelta, datetime


def get_now():
    return timezone.now().timestamp()


def workflow_share_on_linkedin_node(instance):
    try:
        instance.validate_can_share_on_socials()
    except Exception as e:
        print(f"error {e}")
        return (
            False,
            "Problem saving instance, stopping sharing",
        )

    instance = instance.perform_share_on_social(mock=True, save=False)
    return True, "shared on Linkedin"


@inngest_client.create_function(
    fn_id="post_schedular",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="post/post.scheduled"),
)
def post_schedular(ctx: inngest.Context) -> str | Exception:
    try:
        ctx.logger.info(ctx.event.data)

        object_id = ctx.event.data.get("object_id")

        # pylint: disable=no-member
        qs = Post.objects.filter(id=object_id)
        if not qs.exists():
            return "missing"
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
        # instance.share_completed_at = timezone.now()
        # instance.save()

        return "done"
    except Exception as error:
        print(f"something went wrong {error}")
        return "something went wrong"
