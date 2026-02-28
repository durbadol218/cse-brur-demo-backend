from urllib import response
from django.http import FileResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notice
from .serializers import NoticeSerializer, NoticeCreateSerializer
from .permissions import IsAdminOrFaculty, CanDownloadNotice
from django.urls import reverse
from rest_framework import generics, permissions, status


class NoticeListView(generics.ListAPIView):
    queryset = Notice.objects.all().order_by('-date')
    serializer_class = NoticeSerializer
    permission_classes = [permissions.AllowAny]
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context

class NoticeCreateView(generics.CreateAPIView):
    queryset = Notice.objects.all()
    serializer_class = NoticeCreateSerializer
    permission_classes = [IsAdminOrFaculty]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class NoticeDownloadView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, pk):
        try:
            notice = Notice.objects.get(pk=pk)
            file_name = notice.pdf_file.name.split('/')[-1]
            return FileResponse(notice.pdf_file.open(), as_attachment=False, filename=file_name, content_type='application/pdf')
        except Notice.DoesNotExist:
            return Response({"error": "Notice not found"}, status=status.HTTP_404_NOT_FOUND)
        
class NoticeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notice.objects.all()
    serializer_class = NoticeCreateSerializer
    permission_classes = [IsAdminOrFaculty]
    lookup_field = 'pk'