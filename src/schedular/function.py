import inngest
from django.utils import timezone
from .client import inngest_client
from posts.models import Post


@inngest_client.create_function(
    fn_id="post_schedular",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="post/post.scheduled"),
)
def post_schedular(ctx: inngest.Context) -> str:
    ctx.logger.info(ctx.event.data)

    print(ctx.event.data)

    object_id = ctx.event.data.get("object_id")
    try:
        instance = Post.objects.get(id=object_id)
    except Post.DoesNotExist:
        print("missing in the db")
        return "missing"

    share_platforms = instance.scheduled_platform()
    print(share_platforms)
    if "linkedin" in share_platforms:
        # handle linkedin
        try:
            instance.validate_can_share_on_socials()
        except Exception as e:
            print(f"error {e}")
            return "Problem saving instance"
        instance = instance.perform_share_on_social(mock=True, save=False)
        print(share_platforms, str(instance.content)[:10])

    instance.shared_completed_at = timezone.now()
    instance.save()

    return "done"
