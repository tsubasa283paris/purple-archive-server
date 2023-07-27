from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "password",
            "name",
            "created_at",
            "updated_at",
            "deleted_at",
        )
