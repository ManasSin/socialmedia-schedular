import inngest
from django.utils import timezone
from .client import inngest_client
from posts.models import Post
from datetime import timedelta, datetime


def get_now():
    return timezone.now().timestamp()


@inngest_client.create_function(
    fn_id="post_schedular",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="post/post.scheduled"),
)
def post_schedular(ctx: inngest.Context) -> str:
    ctx.logger.info(ctx.event.data)

    print(ctx.event.data)

    object_id = ctx.event.data.get("object_id")

    # pylint: disable=no-member
    qs = Post.objects.filter(id=object_id)
    if not qs.exists():
        return "missing"
    instance = qs.first()

    share_platforms = instance.scheduled_platform()

    if "linkedin" in share_platforms:
        # handle linkedin
        publish_date = instance.share_at + timedelta(seconds=7)
        if instance.share_at:
            publish_date = instance.share_at + timedelta(seconds=7)

        ctx.step.sleep_until("linkedin_sleep_schedular", publish_date)
        try:
            instance.validate_can_share_on_socials()
        except Exception as e:
            print(f"error {e}")
            return "Problem saving instance"

        instance = instance.perform_share_on_social(mock=True, save=False)
        print(share_platforms, str(instance.content)[:10])

    qs.update(share_completed_at=timezone.now())
    # instance.share_completed_at = timezone.now()
    # instance.save()

    return "done"
