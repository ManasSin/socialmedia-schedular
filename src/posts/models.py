from django.utils import timezone
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from helpers import linkedin

User = settings.AUTH_USER_MODEL

# Create your models here.


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    share_on_linkedin = models.BooleanField(default=False)
    shared_at_linkedin = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        if self.share_on_linkedin:
            self.validate_can_share_on_socials()

    def save(self, *args, **kwargs):
        if self.share_on_linkedin:
            self.perform_share_on_social(save=False)
        super().save(*args, **kwargs)

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

    def perform_share_on_social(self, save=False):
        self.share_on_linkedin = False
        # call the actual function to send the content to the linkedin
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
