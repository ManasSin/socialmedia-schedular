import inngest
from django.utils import timezone
from .client import inngest_client
import time
import threading


def delayed_function(message):
    # try:
    #         instance = Post.objects.get(id=object_id)
    #     except Post.DoesNotExist:
    #         return "missing"
    #     share_platforms = instance.get_scheduled_platforms()
    #     print(share_platforms)
    #     if "linkedin" in share_platforms:
    #         # handle linkedin
    #         try:
    #             instance.verify_can_share_on_linkedin()
    #         except Exception as e:
    #             print("error")
    #             return "Problem saving instance"
    #         instance = instance.perform_share_on_linkedin(mock=True, save=False)
    #         print(share_platforms, instance.user, str(instance.content)[:10])

    #     instance.shared_completed_at = timezone.now()
    #     instance.save()
    print(f"Executing after delay: {message}")


@inngest_client.create_function(
    fn_id="post_schedular",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="post/post.scheduled"),
)
def post_schedular(ctx: inngest.Context) -> str:
    ctx.logger.info(ctx.event.data)

    print(ctx.event.data)
    # from posts.models import Post

    # object_id = ctx.event.data.get("object_id")
    try:
        # do something here
        timer = threading.Timer(3, delayed_function, args=["Hello from the future!"])
        timer.start()
    except Exception as e:
        print("error", str(e))
        return "Problem saving instance"
    finally:
        print(f"function completed at : {timezone.now()}")
    return "done"
