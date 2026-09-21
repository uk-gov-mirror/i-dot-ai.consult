from typing import ClassVar

from rest_framework import serializers

from authentication.models import User
from consultations.models import Consultation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields: ClassVar[list] = ["id", "email", "is_staff"]


class ConsultationSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Consultation
        fields: ClassVar[list] = [
            "id",
            "title",
            "code",
            "stage",
            "data_source",
            "users",
            "created_at",
            "running_job",
        ]
