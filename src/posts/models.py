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
        if len(self.content) < 5:
            raise ValidationError(
                {"content": "Content fields should be at least be 5 Char long"}
            )
        if self.share_on_linkedin and not self.can_share_on_linkedin:
            raise ValidationError(
                {"share_on_linkedin": "Content is already shared on linkedin"}
            )

    def save(self, *args, **kwargs):
        if self.share_on_linkedin and self.can_share_on_linkedin:
            print("sharing on linkedin right away")
            # call the actual function to send the content to the linkedin
            try:
                linkedin.share_linkedin(self.user, self.content)
            except Exception as e:
                raise Exception(
                    f"there was some error while making the post, read more :{e}") from e

            self.shared_at_linkedin = timezone.now()
        else:
            print("not sharing")
            # raise Exception("already made a post")
        self.share_on_linkedin = False
        super().save(*args, **kwargs)

    @property
    def can_share_on_linkedin(self):
        try:
            linkedin.get_social_user(self.user, "linkedin")
        # except Exception as e:
            # raise ValidationError({"user": f"{e}"}) from e
            # raise ValidationError({
            #   "user": "User has no validation to social providers"
            # })
        except linkedin.NotConnectedToSocialException as not_connected:
            # pylint: disable=not-callable
            raise not_connected(
                "You must be connect to a social provider to make a social post") from not_connected
        return not self.shared_at_linkedin
