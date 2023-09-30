from django.db import models

class User(models.Model):
    id = models.CharField(
        primary_key=True,
        blank=False,
        unique=True,
        max_length=128,
    )
    password = models.CharField(
        blank=False,
        max_length=128,
    )
    name = models.CharField(
        blank=False,
        max_length=256,
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
