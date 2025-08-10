import inngest
from .client import inngest_client


@inngest_client.create_function(
    fn_id="post_schedular",
    # Event that triggers this function
    trigger=inngest.TriggerEvent(event="post/post.scheduled"),
)
def post_schedular(ctx: inngest.Context) -> str:
    ctx.logger.info(ctx.event)
    print(ctx.event)
    return "done"
