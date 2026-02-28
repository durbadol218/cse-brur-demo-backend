from .views import (
    NoticeListView,
    NoticeCreateView,
    NoticeDownloadView,
    NoticeDetailView
)

from django.urls import path

urlpatterns = [
    path('', NoticeListView.as_view(), name='notice-list'),
    path('create/', NoticeCreateView.as_view(), name='notice-create'),
    path('<int:pk>/download/', NoticeDownloadView.as_view(), name='notice-download'),
    path('<int:pk>/', NoticeDetailView.as_view(), name='notice-detail'),
]