from typing import Any
from django.contrib import admin
from django.http import HttpRequest

# Register your models here.

from .models import Post


class PostAdmin(admin.ModelAdmin):
    list_filter = ["updated_at"]
    list_display = ["user", "content", "updated_at"]
    # pass

    def get_list_display(self, request: HttpRequest):
        if request.user.is_superuser:
            return ["content", "user", "updated_at"]
        # return super().get_list_display(request)
        return ["content", "updated_at"]

    def get_queryset(self, request: HttpRequest):
        # if request.user.is_superuser:
        #     return super().get_queryset(request)
        # return super().get_queryset(request).filter(user=request.user)
        user = request.user
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=user)

    def get_readonly_fields(
        self, request: HttpRequest, obj: Any | None = ...
    ) -> list[str]:
        # print(obj)
        if obj and obj.shared_at_socials:
            return [
                "user",
                "content",
                "shared_at_socials",
                "share_on_socials",
                "share_start_at",
                "share_completed_at",
            ]
        if request.user.is_superuser:
            return ["shared_at_socials", "share_start_at", "share_completed_at"]
        return ["user", "shared_at_socials", "share_now", "share_at"]

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: Any | None = None,
    ) -> bool:
        if request.user.is_superuser:
            return True
        if obj is None:
            return False
        return obj.user == request.user and not obj.shared_at_socials
        # return False

    def save_model(
        self, request: HttpRequest, obj: Any, form: Any, change: Any
    ) -> None:
        # print(form)
        if not change:
            if not obj.user:
                obj.user = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Post, PostAdmin)
