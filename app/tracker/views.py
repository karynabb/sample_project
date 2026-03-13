from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from app.tracker.serializers import QuestionnaireEventsSerializer


class CreateQuestionnaireEventView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    base_serializer = QuestionnaireEventsSerializer

    def get_serializer_class(self):
        for sub_serializer in self.base_serializer.__subclasses__():
            if sub_serializer.Meta.model.action_name == self.request.data["type"]:
                return sub_serializer
        raise ValueError("Incorrect type provided.")

    def create(self, request, *args, **kwargs):
        request.data["user"] = request.user.id
        return super().create(request, *args, **kwargs)
