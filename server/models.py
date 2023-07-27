from django.db import models

class User(models.Model):
    password = models.CharField(
        blank=False,
        max_length=128,
    )
    name = models.CharField(
        blank=False,
        unique=True,
        max_length=128,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    deleted_at = models.DateTimeField(
        default=None,
        blank=True,
        null=True,
    )
