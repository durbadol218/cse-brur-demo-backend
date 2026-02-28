from django.utils import timezone
from rest_framework import serializers
from .models import (SemesterResult, User, USER_ROLE, Profile, UserVerification,Education, Student, Faculty, Staff, Alumni)
from django.db import transaction
from .utils import send_waiting_approval_email
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, Student, Faculty, Staff, Alumni

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    verification_document = serializers.FileField(write_only=True, required=False)
    verification_type = serializers.ChoiceField(
        choices=[
            'student_id', 'faculty_id', 'staff_id', 'certificate', 'others'
        ],
        write_only=True, required=False
    )
    
    student_id = serializers.CharField(write_only=True, required=False)
    session = serializers.CharField(write_only=True, required=False)
    graduation_year = serializers.CharField(write_only=True, required=False)
    current_company = serializers.CharField(write_only=True, required=False)
    linkedin_url = serializers.CharField(write_only=True, required=False)
    designation = serializers.CharField(write_only=True, required=False)
    department = serializers.CharField(write_only=True, required=False)
    degree = serializers.CharField(write_only=True, required=False)
    major = serializers.CharField(write_only=True, required=False)
    institute = serializers.CharField(write_only=True, required=False)
    country = serializers.CharField(write_only=True, required=False, allow_blank=True)
    passing_year = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    # education_details = serializers.CharField(write_only=True, required=False)
    
    def validate_verification_document(self, file):
        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "File size must be under 5MB."
            )
        return file

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'username',
            'password',
            'role',
            'contact_number',
            
            'student_id',
            'session',
            'graduation_year',
            'current_company',
            'linkedin_url',
            
            'designation',
            'department',
            'degree',
            'major',
            'institute',
            'country',
            'passing_year',            
            'verification_document',
            'verification_type',
        ]
    
    def validate(self, data):
        role = data.get('role')
        if not role:
            raise serializers.ValidationError({'role': 'Role is required.'})
        
        if role!= 'admin':
            if not data.get('verification_document'):
                raise serializers.ValidationError({'verification_document': 'Verification document is required.'})
            if not data.get('verification_type'):
                raise serializers.ValidationError({'verification_type': 'Verification type is required.'})
            
        if role == 'student':
            if not data.get('student_id'):
                raise serializers.ValidationError({'student_id': 'Student ID is required for students.'})
            if not data.get('session'):
                raise serializers.ValidationError({'session': 'Session is required for students.'})

        if role == 'alumni':
            gy = data.get('graduation_year')
            if not gy:
                raise serializers.ValidationError({'graduation_year': 'Graduation year is required for alumni.'})
            try:
                year = int(gy)
                if not (1900 <= year <= 2100):
                    raise ValueError
            except ValueError:
                raise serializers.ValidationError({'graduation_year': 'Graduation year must be a valid 4-digit number (1900-2100).'})
            data['graduation_year'] = year
        
        if role == 'faculty':
            if not data.get('designation'):
                raise serializers.ValidationError({'designation': 'Designation is required for faculty.'})
            if not data.get('department'):
                raise serializers.ValidationError({'department': 'Department is required for faculty.'})
        return data
    
    def create(self, validated_data):
        document = validated_data.pop('verification_document', None)
        verification_type = validated_data.pop('verification_type', None)
        student_id = validated_data.pop('student_id', None)
        session = validated_data.pop('session', None)
        graduation_year = validated_data.pop('graduation_year', None)

        current_company = validated_data.pop('current_company', '')
        linkedin_url = validated_data.pop('linkedin_url', '')
        
        designation = validated_data.pop('designation', '')
        department = validated_data.pop('department', '')
        degree = validated_data.pop('degree', '')
        major = validated_data.pop('major', '')
        institute = validated_data.pop('institute', '')
        country = validated_data.pop('country', '')
        passing_year = validated_data.pop('passing_year', None)
        # education_details = validated_data.pop('education_details', '')

        print("Creating faculty with:", {
            'designation': designation,
            'department': department,
            # 'education_details': education_details
        })
        
        # Optional debug print - keep it for now
        print("Creating alumni with:", {
            'graduation_year': graduation_year,
            'current_company': current_company,
            'linkedin_url': linkedin_url
        })

        with transaction.atomic():
            user = User.objects.create_user(
                **validated_data,
                is_active=False,
                is_approved=False
            )
            if user.role == 'admin':
                user.is_approved = True
                user.save()

            profile = Profile.objects.create(user=user)
            send_waiting_approval_email(user)
            if document and verification_type:UserVerification.objects.create(
                user=user,
                verification_type=verification_type,
                document=document
            )
            
            if user.role == 'student':
                batch = None
                if session:
                    try:
                        start_year = int(session.split('-')[0])
                        if 2000 <= start_year <= 2100:
                            batch = start_year - 2007
                    except:
                        pass

                Student.objects.create(
                    profile=profile,
                    student_id=student_id,
                    session=session,
                    batch=str(batch) if batch is not None else '',
                )
            elif user.role == 'alumni':
                Alumni.objects.create(
                    profile=profile,
                    graduation_year=graduation_year,
                    current_company=current_company.strip() if current_company else '',
                    linkedin_url=linkedin_url.strip() if linkedin_url else '',
                    verified=False,
                )
            elif user.role == 'faculty':
                Faculty.objects.create(
                    profile=profile,
                    designation=designation.strip() if designation else '',
                    department=department.strip() if department else '',
                )
                
                if degree.strip() or institute.strip():
                    Education.objects.create(
                        profile=profile,
                        degree=degree.strip(),
                        major=major.strip(),
                        institute=institute.strip(),
                        country=country.strip(),
                        passing_year=passing_year,
                    )

        return user
    
    
    def to_representation(self, instance):
        return {
            "id": instance.id,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            "email": instance.email,
            "username": instance.username,
            "role": instance.role,
            "is_approved": instance.is_approved,
            "message": "Registration successful! Your account is pending admin approval. You will be notified by email once approved. You cannot log in until then."
        }


User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['address', 'profile_image', 'joined_date']
        read_only_fields = fields

    def get_profile_image(self, obj):
        if obj.profile_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.profile_image.url)
        return None
    
    def get_role_specific(self, obj):
        profile = obj.profile
        if obj.role == 'student' and hasattr(profile, 'student'):
            return {'student': StudentProfileSerializer(profile.student).data}
        elif obj.role == 'alumni' and hasattr(profile, 'alumni'):
            return {'alumni': AlumniProfileSerializer(profile.alumni).data}
        # ... faculty, staff ...
        return None

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['student_id', 'session', 'batch', 'status']


class AlumniProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumni
        fields = ['graduation_year', 'current_company', 'linkedin_url', 'verified']


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['degree', 'major', 'institute', 'country', 'passing_year']

class FacultyProfileSerializer(serializers.ModelSerializer):
    education = EducationSerializer(
        source='profile.education_records',
        many=True,
        read_only=True
    )

    class Meta:
        model = Faculty
        fields = [
            'designation',
            'department',
            'education',
        ]

class StaffProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['position', 'office']


class StudentRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['student_id', 'session', 'batch', 'status']
        read_only_fields = ['status']

class AlumniRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumni
        fields = ['graduation_year', 'current_company', 'linkedin_url']

class FacultyRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ['designation', 'department']

class StaffRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['position', 'office']


class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    role_specific = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'username',
            'role', 'contact_number', 'is_approved',
            'profile', 'role_specific',
        ]
        read_only_fields = ['role', 'is_approved', 'email', 'username']

    def get_role_specific(self, obj):
        try:
            profile = obj.profile
        except Profile.DoesNotExist:
            return None

        if obj.role == 'student' and hasattr(profile, 'student'):
            return {'student': StudentProfileSerializer(profile.student).data}
        elif obj.role == 'alumni' and hasattr(profile, 'alumni'):
            return {'alumni': AlumniProfileSerializer(profile.alumni).data}
        elif obj.role == 'faculty' and hasattr(profile, 'faculty_member'):
            faculty_serializer = FacultyProfileSerializer(profile.faculty_member, context=self.context)
            return {'faculty': faculty_serializer.data}
        elif obj.role == 'staff' and hasattr(profile, 'staff'):
            return {'staff': StaffProfileSerializer(profile.staff).data}
        
        return None
    
    
class ProfileUpdateSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Profile
        fields = ['address', 'profile_image']


class AlumniUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumni
        fields = ['graduation_year', 'current_company', 'linkedin_url']
        extra_kwargs = {
            'graduation_year': {'required': False},
            'current_company': {'required': False},
            'linkedin_url': {'required': False},
        }

class FacultyUpdateSerializer(serializers.ModelSerializer):
    education = EducationSerializer(
        source='profile.education_records',
        many=True,
        required=False,
        write_only=True  # only accept input, don't return in response
    )

    class Meta:
        model = Faculty
        fields = [
            'designation',
            'department',
            'education',          # ← new: accept list of education records
        ]
        extra_kwargs = {
            'designation': {'required': False},
            'department': {'required': False},
        }

    def update(self, instance, validated_data):
        # Pop education data
        education_data = validated_data.pop('education', None)

        # Update basic faculty fields
        instance.designation = validated_data.get('designation', instance.designation)
        instance.department = validated_data.get('department', instance.department)
        instance.save()

        # Handle education records (create/update/delete)
        if education_data is not None:
            # Optional: delete old records if you want to replace completely
            instance.profile.education_records.all().delete()

            for edu_item in education_data:
                Education.objects.update_or_create(
                    profile=instance.profile,
                    degree=edu_item.get('degree'),
                    defaults={
                        'major': edu_item.get('major', ''),
                        'institute': edu_item.get('institute', ''),
                        'country': edu_item.get('country', ''),
                        'passing_year': edu_item.get('passing_year'),
                    }
                )

        return instance


class UserUpdateSerializer(serializers.ModelSerializer):
    profile = ProfileUpdateSerializer(required=False)
    
    alumni = AlumniUpdateSerializer(required=False, source='profile.alumni', read_only=False)
    faculty = FacultyUpdateSerializer(required=False, source='profile.faculty', read_only=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'contact_number', 'profile', 'alumni', 'faculty']
        read_only_fields = ['role', 'is_approved', 'email', 'username']

    def update(self, instance, validated_data):
        print("Raw validated_data before pop:", validated_data)

        profile_data = validated_data.pop('profile', None)
        alumni_data = validated_data.pop('alumni', None)
        faculty_data = None

        if profile_data:
            faculty_data = profile_data.pop('faculty', None)
            alumni_data = profile_data.pop('alumni', None)

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.contact_number = validated_data.get('contact_number', instance.contact_number)
        instance.save()

        if profile_data:
            profile_serializer = ProfileUpdateSerializer(
                instance.profile,
                data=profile_data,
                partial=True,
                context=self.context
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        print("Faculty data extracted:", faculty_data)

        if faculty_data and instance.role == 'faculty':
            faculty = None
            try:
                faculty = instance.profile.faculty_member
                print("Found existing Faculty object")
            except Faculty.DoesNotExist:
                print("Creating new Faculty object for user:", instance.username)
                faculty = Faculty.objects.create(profile=instance.profile)

            if faculty:
                faculty_serializer = FacultyUpdateSerializer(
                    faculty,
                    data=faculty_data,
                    partial=True,
                    context=self.context
                )
                faculty_serializer.is_valid(raise_exception=True)
                faculty_serializer.save()
                print("Faculty updated successfully")

        if alumni_data and instance.role == 'alumni':
            alumni = None
            try:
                alumni = instance.profile.alumni
            except Alumni.DoesNotExist:
                print("Creating new Alumni object for user:", instance.username)
                alumni = Alumni.objects.create(profile=instance.profile)

            if alumni:
                alumni_serializer = AlumniUpdateSerializer(
                    alumni,
                    data=alumni_data,
                    partial=True,
                    context=self.context
                )
                alumni_serializer.is_valid(raise_exception=True)
                alumni_serializer.save()

        return instance

class FacultyUpdateSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Faculty
        fields = ['designation', 'department']

    def update(self, instance, validated_data):
        instance.designation = validated_data.get('designation', instance.designation)
        instance.department = validated_data.get('department', instance.department)
        instance.save()
        request_data = self.context['request'].data

        education_list = []
        index = 0
        while True:
            degree_key = f'faculty.education[{index}][degree]'
            if degree_key not in request_data:
                break

            edu = {
                'degree': request_data.get(degree_key, '').strip(),
                'major': request_data.get(f'faculty.education[{index}][major]', '').strip(),
                'institute': request_data.get(f'faculty.education[{index}][institute]', '').strip(),
                'country': request_data.get(f'faculty.education[{index}][country]', '').strip(),
                'passing_year': request_data.get(f'faculty.education[{index}][passing_year]', None) or None,
            }

            if edu['degree'] or edu['institute']:
                education_list.append(edu)

            index += 1

        if education_list:
            print("Parsed education_list:", education_list)
            instance.profile.education_records.all().delete()
            for edu in education_list:
                Education.objects.create(
                    profile=instance.profile,
                    degree=edu['degree'],
                    major=edu['major'],
                    institute=edu['institute'],
                    country=edu['country'],
                    passing_year=edu['passing_year'],
                )
        else:
            print("No valid education data received")

        return instance
    
class FacultyDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.CharField(source='profile.user.email', read_only=True)
    contact_number = serializers.CharField(source='profile.user.contact_number', read_only=True, allow_null=True)
    profile_image = serializers.SerializerMethodField()
    biography = serializers.CharField(default="No biography available", read_only=True)
    education = EducationSerializer(source='profile.education_records', many=True, read_only=True)

    class Meta:
        model = Faculty
        fields = [
            'id', 'full_name', 'designation', 'department',
            'email', 'contact_number', 'profile_image', 'biography',
            'education',
        ]

    def get_full_name(self, obj):
        user = obj.profile.user
        return f"{user.first_name} {user.last_name}".strip() or user.username

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile.profile_image:
            return request.build_absolute_uri(obj.profile.profile_image.url)
        return None
    
class FacultyListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.CharField(source='profile.user.email')
    contact_number = serializers.CharField(source='profile.user.contact_number', allow_null=True)
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Faculty
        fields = [
            'id',
            'full_name',
            'designation',
            'department',
            'email',
            'contact_number',
            'profile_image',
        ]

    def get_full_name(self, obj):
        user = obj.profile.user
        return f"{user.first_name} {user.last_name}".strip() or user.username

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile.profile_image:
            return request.build_absolute_uri(obj.profile.profile_image.url)
        return None
    

class UserAdminListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_specific_summary = serializers.SerializerMethodField()
    is_approved_display = serializers.CharField(source='is_approved', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'contact_number', 'is_approved', 'is_approved_display',
            'full_name', 'role_specific_summary', 'date_joined'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_role_specific_summary(self, obj):
        try:
            profile = obj.profile
        except Profile.DoesNotExist:
            return "No profile"

        if obj.role == 'student' and hasattr(profile, 'student'):
            s = profile.student
            return f"Student ID: {s.student_id} | Session: {s.session or 'N/A'} | Status: {s.status}"
        elif obj.role == 'faculty' and hasattr(profile, 'faculty_member'):
            f = profile.faculty_member
            return f"Designation: {f.designation} | Department: {f.department}"
        elif obj.role == 'alumni' and hasattr(profile, 'alumni'):
            a = profile.alumni
            return f"Graduation: {a.graduation_year} | Company: {a.current_company or 'N/A'}"
        elif obj.role == 'staff' and hasattr(profile, 'staff'):
            s = profile.staff
            return f"Position: {s.position} | Office: {s.office}"
        return "—"


class UserAdminDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    role_specific = serializers.SerializerMethodField()
    verifications = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'contact_number', 'is_approved', 'date_joined',
            'profile', 'role_specific', 'verifications'
        ]
        read_only_fields = ['email', 'username', 'date_joined']

    def get_role_specific(self, obj):
        try:
            profile = obj.profile
        except Profile.DoesNotExist:
            return None

        if obj.role == 'student' and hasattr(profile, 'student'):
            return {'student': StudentProfileSerializer(profile.student).data}
        elif obj.role == 'alumni' and hasattr(profile, 'alumni'):
            return {'alumni': AlumniProfileSerializer(profile.alumni).data}
        elif obj.role == 'faculty' and hasattr(profile, 'faculty_member'):
            return {'faculty': FacultyProfileSerializer(profile.faculty_member, context=self.context).data}
        elif obj.role == 'staff' and hasattr(profile, 'staff'):
            return {'staff': StaffProfileSerializer(profile.staff).data}
        return None

    def get_verifications(self, obj):
        return [{
            'type': v.verification_type,
            'document': v.document.url if v.document else None,
            'is_verified': v.is_verified,
            'submitted_at': v.submitted_at,
            'remarks': v.remarks
        } for v in obj.verifications.all()]


class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    role = serializers.ChoiceField(choices=USER_ROLE, required=True)
    is_approved = serializers.BooleanField(default=True)
    
    student_id = serializers.CharField(required=False, allow_blank=True)
    session = serializers.CharField(required=False, allow_blank=True)
    graduation_year = serializers.IntegerField(required=False, allow_null=True)
    current_company = serializers.CharField(required=False, allow_blank=True)
    linkedin_url = serializers.URLField(required=False, allow_blank=True)
    designation = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    position = serializers.CharField(required=False, allow_blank=True)
    office = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'username', 'password',
            'role', 'contact_number', 'is_approved',
            'student_id', 'session',
            'graduation_year', 'current_company', 'linkedin_url',
            'designation', 'department',
            'position', 'office',
        ]

    def validate(self, data):
        role = data.get('role')

        if role == 'student':
            if not data.get('student_id'):
                raise serializers.ValidationError({'student_id': 'Required for students'})
            if not data.get('session'):
                raise serializers.ValidationError({'session': 'Required for students'})

        elif role == 'alumni':
            gy = data.get('graduation_year')
            if gy is None or gy == '':
                raise serializers.ValidationError({'graduation_year': 'Required for alumni'})
            if not isinstance(gy, int):
                try:
                    data['graduation_year'] = int(gy)
                except (ValueError, TypeError):
                    raise serializers.ValidationError({'graduation_year': 'Must be a valid integer'})
            if not (1900 <= data['graduation_year'] <= 2100):
                raise serializers.ValidationError({'graduation_year': 'Must be between 1900 and 2100'})
        elif role == 'faculty':
            if not data.get('designation'):
                raise serializers.ValidationError({'designation': 'Required for faculty'})
            if not data.get('department'):
                raise serializers.ValidationError({'department': 'Required for faculty'})

        elif role == 'staff':
            if not data.get('position'):
                raise serializers.ValidationError({'position': 'Required for staff'})
            if not data.get('office'):
                raise serializers.ValidationError({'office': 'Required for staff'})

        return data

    def create(self, validated_data):
        student_id = validated_data.pop('student_id', None)
        session = validated_data.pop('session', None)
        graduation_year = validated_data.pop('graduation_year', None)
        current_company = validated_data.pop('current_company', '')
        linkedin_url = validated_data.pop('linkedin_url', '')
        designation = validated_data.pop('designation', '')
        department = validated_data.pop('department', '')
        position = validated_data.pop('position', '')
        office = validated_data.pop('office', '')

        user = User.objects.create_user(
            **validated_data,
            is_active=True,
            # is_approved=True
        )
        user.is_approved = True
        user.save(update_fields=['is_approved'])

        profile = Profile.objects.create(user=user)
        send_waiting_approval_email(user)
        if user.role == 'student' and student_id and session:
            Student.objects.create(profile=profile, student_id=student_id, session=session)

        elif user.role == 'alumni' and graduation_year:
            Alumni.objects.create(
                profile=profile,
                graduation_year=graduation_year,
                current_company=current_company.strip(),
                linkedin_url=linkedin_url.strip(),
                verified=False,
            )

        elif user.role == 'faculty' and designation and department:
            Faculty.objects.create(
                profile=profile,
                designation=designation.strip(),
                department=department.strip(),
            )

        elif user.role == 'staff' and position and office:
            Staff.objects.create(
                profile=profile,
                position=position.strip(),
                office=office.strip(),
            )

        return user


# ───────────────────────────────────────────────
# 2. Admin Update User Serializer (Edit any user)
# ───────────────────────────────────────────────
# class UserAdminUpdateSerializer(serializers.ModelSerializer):
#     profile = ProfileUpdateSerializer(required=False)
#     role = serializers.ChoiceField(choices=USER_ROLE, required=False)
#     is_approved = serializers.BooleanField(required=False)

#     # Role-specific nested fields (source points to related model)
#     student_id = serializers.CharField(source='profile.student.student_id', required=False, allow_blank=True)
#     session = serializers.CharField(source='profile.student.session', required=False, allow_blank=True)
#     graduation_year = serializers.IntegerField(source='profile.alumni.graduation_year', required=False, allow_null=True)
#     current_company = serializers.CharField(source='profile.alumni.current_company', required=False, allow_blank=True)
#     linkedin_url = serializers.URLField(source='profile.alumni.linkedin_url', required=False, allow_blank=True)
#     designation = serializers.CharField(source='profile.faculty_member.designation', required=False, allow_blank=True)
#     department = serializers.CharField(source='profile.faculty_member.department', required=False, allow_blank=True)
#     position = serializers.CharField(source='profile.staff.position', required=False, allow_blank=True)
#     office = serializers.CharField(source='profile.staff.office', required=False, allow_blank=True)

#     class Meta:
#         model = User
#         fields = [
#             'first_name', 'last_name', 'contact_number',
#             'role', 'is_approved', 'profile',
#             'student_id', 'session',
#             'graduation_year', 'current_company', 'linkedin_url',
#             'designation', 'department',
#             'position', 'office',
#         ]
#         read_only_fields = ['email', 'username']

#     def update(self, instance, validated_data):
#         profile_data = validated_data.pop('profile', None)

#         # Pop role-specific fields
#         student_id = validated_data.pop('student_id', None)
#         session = validated_data.pop('session', None)
#         graduation_year = validated_data.pop('graduation_year', None)
#         current_company = validated_data.pop('current_company', None)
#         linkedin_url = validated_data.pop('linkedin_url', None)
#         designation = validated_data.pop('designation', None)
#         department = validated_data.pop('department', None)
#         position = validated_data.pop('position', None)
#         office = validated_data.pop('office', None)

#         # Update basic user fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # Update profile if provided
#         if profile_data:
#             profile_serializer = ProfileUpdateSerializer(
#                 instance.profile, data=profile_data, partial=True, context=self.context
#             )
#             profile_serializer.is_valid(raise_exception=True)
#             profile_serializer.save()

#         # Update role-specific objects (only if role matches current)
#         if instance.role == 'student' and hasattr(instance.profile, 'student'):
#             student = instance.profile.student
#             if student_id is not None:
#                 student.student_id = student_id
#             if session is not None:
#                 student.session = session
#             student.save()

#         elif instance.role == 'alumni' and hasattr(instance.profile, 'alumni'):
#             alumni = instance.profile.alumni
#             if graduation_year is not None:
#                 alumni.graduation_year = graduation_year
#             if current_company is not None:
#                 alumni.current_company = current_company
#             if linkedin_url is not None:
#                 alumni.linkedin_url = linkedin_url
#             alumni.save()

#         elif instance.role == 'faculty' and hasattr(instance.profile, 'faculty_member'):
#             faculty = instance.profile.faculty_member
#             if designation is not None:
#                 faculty.designation = designation
#             if department is not None:
#                 faculty.department = department
#             faculty.save()

#         elif instance.role == 'staff' and hasattr(instance.profile, 'staff'):
#             staff = instance.profile.staff
#             if position is not None:
#                 staff.position = position
#             if office is not None:
#                 staff.office = office
#             staff.save()

#         return instance
    

from .utils import send_verification_approval_email, send_account_approval_email  # your email utils

# ───────────────────────────────────────────────
# Admin Update User Serializer (Edit any user safely)
# ───────────────────────────────────────────────
class UserAdminUpdateSerializer(serializers.ModelSerializer):
    profile = ProfileUpdateSerializer(required=False)
    role = serializers.ChoiceField(choices=USER_ROLE, required=False)
    is_approved = serializers.BooleanField(required=False)

    student = StudentRoleSerializer(required=False, source='profile.student')
    alumni = AlumniRoleSerializer(required=False, source='profile.alumni')
    faculty = FacultyRoleSerializer(required=False, source='profile.faculty_member')
    staff = StaffRoleSerializer(required=False, source='profile.staff')

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'contact_number',
            'role', 'is_approved', 'profile',
            'student', 'alumni', 'faculty', 'staff',
        ]
        read_only_fields = ['email', 'username']

    def validate(self, data):
        """
        Validate role change and required fields.
        """
        if 'role' in data and data['role'] != self.instance.role:
            new_role = data['role']

            if new_role == 'student':
                student_data = data.get('student', {})
                if not student_data.get('student_id'):
                    raise serializers.ValidationError({
                        'student.student_id': 'Required when changing to student role'
                    })
                if not student_data.get('session'):
                    raise serializers.ValidationError({
                        'student.session': 'Required when changing to student role'
                    })

            elif new_role == 'alumni':
                alumni_data = data.get('alumni', {})
                if not alumni_data.get('graduation_year'):
                    raise serializers.ValidationError({
                        'alumni.graduation_year': 'Required when changing to alumni role'
                    })
                year = alumni_data.get('graduation_year')
                if not (1900 <= year <= 2100):
                    raise serializers.ValidationError({
                        'alumni.graduation_year': 'Must be between 1900 and 2100'
                    })
        return data

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        student_data = validated_data.pop('student', None)
        alumni_data = validated_data.pop('alumni', None)
        faculty_data = validated_data.pop('faculty', None)
        staff_data = validated_data.pop('staff', None)

        old_approved = instance.is_approved
        old_role = instance.role

        # Update basic user fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.contact_number = validated_data.get('contact_number', instance.contact_number)
        instance.role = validated_data.get('role', instance.role)
        if 'is_approved' in validated_data:
            instance.is_approved = validated_data['is_approved']
            instance.is_active = validated_data['is_approved']
        instance.save()

        # Update profile if provided
        if profile_data:
            profile_serializer = ProfileUpdateSerializer(
                instance.profile, data=profile_data, partial=True, context=self.context
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        if instance.role != old_role:
            if old_role == 'student' and hasattr(instance.profile, 'student'):
                instance.profile.student.delete()
            elif old_role == 'alumni' and hasattr(instance.profile, 'alumni'):
                instance.profile.alumni.delete()
            elif old_role == 'faculty' and hasattr(instance.profile, 'faculty_member'):
                instance.profile.faculty_member.delete()
            elif old_role == 'staff' and hasattr(instance.profile, 'staff'):
                instance.profile.staff.delete()

            if instance.role == 'student':
                Student.objects.create(profile=instance.profile)
            elif instance.role == 'alumni':
                Alumni.objects.create(profile=instance.profile)
            elif instance.role == 'faculty':
                Faculty.objects.create(profile=instance.profile)
            elif instance.role == 'staff':
                Staff.objects.create(profile=instance.profile)

        if instance.role == 'student' and hasattr(instance.profile, 'student'):
            student = instance.profile.student
            if student_data:
                for key, value in student_data.items():
                    if value is not None:
                        setattr(student, key, value)
                student.save()

        # Repeat similar logic for alumni, faculty, staff if needed...

        if 'is_approved' in validated_data and instance.is_approved != old_approved:
            send_account_approval_email(
                user=instance,
                is_approved=instance.is_approved,
                remarks=validated_data.get('remarks')
            )
        return instance
    
    
class VerificationSerializer(serializers.ModelSerializer):
    document_url = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserVerification
        fields = [
            'id', 'user_email', 'verification_type',
            'document_url', 'is_verified', 'submitted_at',
            'reviewed_at', 'remarks'
        ]

    def get_document_url(self, obj):
        request = self.context.get('request')
        if obj.document:
            return request.build_absolute_uri(obj.document.url)
        return None


class VerificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerification
        fields = ['is_verified', 'remarks']
        read_only_fields = ['reviewed_at']

    def update(self, instance, validated_data):
        old_status = instance.is_verified
        
        instance.is_verified = validated_data.get('is_verified', instance.is_verified)
        instance.remarks = validated_data.get('remarks', instance.remarks)
        instance.reviewed_at = timezone.now()
        instance.reviewed_by = self.context['request'].user
        instance.save()

        if instance.is_verified != old_status:
            send_verification_approval_email(
                instance,
                is_verified=instance.is_verified,
                remarks=instance.remarks
            )

        return instance

class SemesterResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemesterResult
        fields = ['id', 'semester', 'sgpa', 'cgpa', 'result_status', 'uploaded_at']