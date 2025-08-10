import inngest
import inngest.django

from .client import inngest_client
from .function import post_schedular

schedular_inngest_view_path = inngest.django.serve(
    # app,
    inngest_client,
    [post_schedular],
)
