from typing import ClassVar

from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations.api.permissions import CanSeeConsultation
from consultations.models import Consultation

from .serializers import ConsultationSerializer


class ConsultationViewSet(ReadOnlyModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultation | IsAdminUser]

    def get_queryset(self):
        queryset = Consultation.objects.prefetch_related("users").order_by("-created_at")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(users=self.request.user)
