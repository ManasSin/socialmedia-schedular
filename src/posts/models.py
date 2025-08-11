from django.utils import timezone
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta

from helpers import linkedin

from schedular.healper import trigger_inngest_events

User = settings.AUTH_USER_MODEL

# Create your models here.


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    share_now = models.BooleanField(default=None, null=True, blank=True)
    share_at = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True, blank=True
    )
    shared_completed_at = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True, blank=True
    )
    share_on_linkedin = models.BooleanField(default=False)
    shared_at_linkedin = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        if all(
            [
                self.share_now is None and self.share_at is None,
                self.shared_completed_at is None,
            ]
        ):
            raise ValidationError(
                {
                    "share_at": "You select a time to schedule the post or must share it now ",
                    "share_now": "You select a time to schedule the post or must share it now ",
                }
            )
        if self.share_on_linkedin:
            self.validate_can_share_on_socials()

    def scheduled_platform(self):
        platform = []
        if self.share_on_linkedin:
            platform.append("linkedin")
        return platform

    def save(self, *args, **kwargs):
        trigger_send = False
        if self.share_on_linkedin:
            # self.perform_share_on_social(save=False)
            print("object_id", self.id)
            trigger_send = True
        super().save(*args, **kwargs)

        if trigger_send:
            time_delay = (timezone.now() + timedelta(seconds=10)).timestamp() * 1000
            if self.share_now:
                time_delay = (timezone.now() + timedelta(seconds=22)).timestamp() * 1000
            elif self.share_at:
                time_delay = (self.share_at + timedelta(seconds=22)).timestamp() * 1000

            trigger_inngest_events(
                "post/post.scheduled",
                {"object_id": self.id},
                id=f"post/post.scheduled/{self.id}",
                ts=int(time_delay),
            )

    def validate_can_share_on_socials(self):
        if len(self.content) < 5:
            raise ValidationError(
                {"content": "Content fields should be at least be 5 Char long"}
            )
        if self.shared_at_linkedin:
            raise ValidationError(
                {"share_on_linkedin": "Content is already shared on linkedin"}
            )
        try:
            linkedin.get_social_user(self.user, "linkedin")
        except linkedin.NotConnectedToSocialException as not_connect:
            raise ValidationError(
                {
                    "user": "You must be connect to a social provider to make a social post"
                }
            ) from not_connect
        except Exception as e:
            raise ValidationError({"user": f"{e}"}) from e

    def perform_share_on_social(self, mock=False, save=False):
        self.share_on_linkedin = False

        if self.shared_at_linkedin:
            return self
        # call the actual function to send the content to the linkedin
        if not mock:
            try:
                linkedin.share_linkedin(self.user, self.content)

            except Exception as e:
                # pylint: disable=broad-exception-raised
                raise Exception(
                    f"there was some error while making the post, read more :{e}"
                ) from e
        self.shared_at_linkedin = timezone.now()
        if save:
            self.save()
        return self
