from django.db import models
from django.conf import settings

# Create your models here.
class Notice(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General Notice'),
        ('exam', 'Exam & Result'),
        ('admission', 'Admission Notice'),
        ('event', 'Event & Seminar'),
        ('scholarship', 'Scholarship'),
        ('job', 'Job Notice'),
        ('other', 'Other'),
    ]
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20,choices=CATEGORY_CHOICES, default='general')
    date = models.DateField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='notices/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_notices'
    )

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"