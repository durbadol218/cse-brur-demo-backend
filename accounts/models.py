from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.conf import settings

# =========================
# USER ROLE CHOICES
# =========================
USER_ROLE = (
    ('admin', 'Admin'),
    ('faculty', 'Faculty'),
    ('student', 'Student'),
    ('staff', 'Staff'),
    ('alumni', 'Alumni'),
)

# =========================
# CUSTOM USER MODEL
# =========================
class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=USER_ROLE
    )

    contact_number = models.CharField(
    max_length=15,
    validators=[RegexValidator(r'^\+?\d{10,15}$')],
    blank=True,
    null=True
)

    is_approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"
    
    def save(self, *args, **kwargs):
        if self.role == 'admin':
            self.is_approved = True
            self.is_staff = True
            # self.is_superuser = True
        super().save(*args, **kwargs)


# =========================
# COMMON PROFILE
# =========================
class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    address = models.CharField(max_length=255, blank=True)
    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.email

class Education(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='education_records'
    )
    
    degree = models.CharField(max_length=100, help_text="e.g. Ph.D., M.Sc., B.Sc.")
    major = models.CharField(max_length=200, help_text="e.g. Computer Science, Applied Physics")
    institute = models.CharField(max_length=200, help_text="e.g. University of Dhaka")
    country = models.CharField(max_length=100, blank=True)
    passing_year = models.PositiveIntegerField(help_text="Year of completion")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-passing_year']
        verbose_name_plural = "Education Records"

    def __str__(self):
        return f"{self.degree} - {self.major} ({self.passing_year})"
    
# =========================
# STUDENT MODEL
# =========================
class Student(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='student'
    )

    student_id = models.CharField(max_length=20, unique=True)
    
    session = models.CharField(
        max_length=20,
        help_text="e.g. 2008-09",
        null=True,
        blank=True
    )
    batch = models.CharField(
    max_length=10,
    blank=True,
    editable=False,
    help_text="Automatically calculated from session (e.g. 2008-09 → 1)"
)

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    def __str__(self):
        return self.student_id


# =========================
# TEACHER / FACULTY MODEL
# =========================
class Faculty(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='faculty_member'
    )

    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    # education_details = models.TextField()
    # biography = models.TextField()

    def __str__(self):
        return self.profile.user.email


# =========================
# STAFF MODEL
# =========================
class Staff(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='staff'
    )

    position = models.CharField(max_length=100)
    office = models.CharField(max_length=100)

    def __str__(self):
        return self.profile.user.email


# =========================
# ALUMNI MODEL
# =========================
class Alumni(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='alumni'
    )

    graduation_year = models.PositiveIntegerField()
    current_company = models.CharField(max_length=150, blank=True)
    linkedin_url = models.URLField(blank=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.profile.user.email


# =========================
# USER VERIFICATION MODEL
# =========================
VERIFICATION_TYPE = (
    ('student_id', 'Student ID Card'),
    ('faculty_id', 'Faculty ID Card'),
    ('staff_id', 'Staff ID Card'),
    ('certificate', 'Certificate'),
    ('others', 'Others'),
)

class UserVerification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verifications'
    )

    verification_type = models.CharField(
        max_length=30,
        choices=VERIFICATION_TYPE
    )

    document = models.FileField(
        upload_to='verification_documents/'
    )

    is_verified = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verifications'
    )

    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.verification_type}"
    
class SemesterResult(models.Model):
    SEMESTER_CHOICES = [
        ('1-1', '1st Year 1st Semester'),
        ('1-2', '1st Year 2nd Semester'),
        ('2-1', '2nd Year 1st Semester'),
        ('2-2', '2nd Year 2nd Semester'),
        ('3-1', '3rd Year 1st Semester'),
        ('3-2', '3rd Year 2nd Semester'),
        ('4-1', '4th Year 1st Semester'),
        ('4-2', '4th Year 2nd Semester'),
    ]
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE,related_name='semester_results')
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4,decimal_places=2, null=True, blank=True)
    result_status = models.CharField(
        max_length=20,
        choices=[('promoted', 'Promoted'), ('not promoted', 'Not Promoted'), ('withdrawn', 'Withdrawn')],
        default='promoted'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.student.student_id} - {self.semester} - SGPA: {self.sgpa} - CGPA: {self.cgpa}"