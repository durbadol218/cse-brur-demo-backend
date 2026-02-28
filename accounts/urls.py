from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from .views import (
    RegisterView,
    UserListView,
    VerificationStatusView,
    PendingVerificationListView,
    ReviewVerificationView,
    ProfileView,
    ProfileUpdateView,
    FacultyListView,
    FacultyDetailView,
    AdminUserListView,
    AdminUserDetailView,
    AdminApproveUserView,
    AdminCreateUserView,
    AdminUserVerificationListView,
    AdminUserVerificationDetailView,
    AdminResultUploadView,
    StudentResultsView
)

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view()),
    path('login/', TokenObtainPairView.as_view(),name='get_token'),
    path('token/refresh/', TokenRefreshView.as_view(),name="refresh_token"),
    path('logout/', TokenRefreshView.as_view(),name="logout"),
    path('list/', UserListView.as_view(), name='list'),
    # Verification
    path('verification/status/', VerificationStatusView.as_view()),
    #profile
    path('student-results/', StudentResultsView.as_view(), name='student-results'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('faculty/', FacultyListView.as_view(), name='faculty-list'),
    path('faculty/<int:id>/', FacultyDetailView.as_view(), name='faculty-detail'),
    # Admin
    path('admin/verifications/', PendingVerificationListView.as_view()),
    path('admin/verifications/<int:pk>/', ReviewVerificationView.as_view()),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:id>/approve/', AdminApproveUserView.as_view(), name='admin-approve-user'),
    
    path('admin/users/create/', AdminCreateUserView.as_view(), name='admin-user-create'),
    path('admin/result-notice-upload/', AdminResultUploadView.as_view(), name='admin-result-notice-upload'),
    path('admin/users/<int:user_id>/verifications/', AdminUserVerificationListView.as_view(), name='admin-user-verifications'),
    path('admin/users/<int:user_id>/verifications/<int:id>/', AdminUserVerificationDetailView.as_view(), name='admin-user-verification-detail'),
    
    # # Bulk approve all verifications for a user
    # path('admin/users/<int:user_id>/verifications/approve-all/', AdminApproveAllVerificationsView.as_view(), name='admin-approve-all-verifications'),
]