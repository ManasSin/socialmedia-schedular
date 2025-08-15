from django.utils import timezone
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta

from helpers import linkedin

from schedular.healper import trigger_inngest_events

User = settings.AUTH_USER_MODEL


# Create your models here.
class SocialPlatform(models.TextChoices):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    share_now = models.BooleanField(default=None, null=True, blank=True)
    share_at = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True, blank=True
    )
    share_start_at = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True, blank=True
    )
    share_completed_at = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True, blank=True
    )
    share_on_socials = models.JSONField(default=list, choices=SocialPlatform.choices)
    shared_at_socials = models.JSONField(default=list, choices=SocialPlatform.choices)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        if all(
            [
                self.share_now is None and self.share_at is None,
                self.share_completed_at is None,
            ]
        ):
            raise ValidationError(
                {
                    "share_at": "You select a time to schedule the post or must share it now ",
                    "share_now": "You select a time to schedule the post or must share it now ",
                }
            )
        if self.share_on_socials:
            self.validate_can_share_on_socials()

    def scheduled_platform(self):
        platform = []
        if self.share_on_socials:
            platform.append(self.share_on_socials)
        return platform

    def save(self, *args, **kwargs):
        trigger_send = False
        if all(
            [
                self.share_now is not None or self.share_at is not None,
                self.share_completed_at is None and self.share_start_at is None,
            ]
        ):
            trigger_send = True

        if self.share_now:
            self.share_at = timezone.now()
        super().save(*args, **kwargs)

        if trigger_send:
            time_delay = (timezone.now() + timedelta(seconds=3)).timestamp() * 1000
            if self.share_at:
                time_delay = (self.share_at + timedelta(seconds=5)).timestamp() * 1000

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
        if self.shared_at_socials:
            raise ValidationError(
                {"share_on_socials": "Content is already shared on social platforms"}
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
        self.share_on_socials = []

        if self.shared_at_socials:
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
        if save:
            self.save()
            self.shared_at_socials = timezone.now()
        return self
