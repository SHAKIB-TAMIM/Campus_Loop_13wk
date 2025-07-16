from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    id_card = models.ImageField(upload_to='id_cards/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    university = models.CharField(max_length=200, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=50)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} about {self.subject}"


class AcademicResource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('lecture_notes', 'Lecture Notes'),
        ('question_papers', 'Question Papers'),
        ('study_guides', 'Study Guides'),
        ('online_courses', 'Online Courses'),
    ]
    
    COURSE_CHOICES = [
        ('MATH101', 'Calculus I'),
        ('MATH201', 'Calculus II'),
        ('PHYS201', 'Physics for Engineers'),
        ('CS101', 'Introduction to Computer Science'),
        ('CS201', 'Data Structures'),
        ('CHEM301', 'Organic Chemistry'),
        ('HIST101', 'World History'),
        ('BUS202', 'Business Management'),
        ('ENG101', 'English Composition'),
        ('BIO101', 'Biology'),
        ('ECON101', 'Microeconomics'),
        ('PSYCH101', 'Introduction to Psychology'),
        ('MATH102', 'Linear Algebra'),
        ('MATH202', 'Differential Equations'),
        ('MATH302', 'Probability and Statistics'),
        ('MATH402', 'Numerical Analysis'),
        ('MATH112', 'Discrete Mathematics'),
        ('MATH322', 'Real Analysis'),
        ('MATH323', 'Complex Analysis'),
    ]
    
    SEMESTER_CHOICES = [
        ('1-I', 'Level - Term: 1 - I'),
        ('1-II', 'Level - Term: 1 - II'),
        ('2-I', 'Level - Term: 2 - I'),
        ('2-II', 'Level - Term: 2 - II'),
        ('3-I', 'Level - Term: 3 - I'),
        ('3-II', 'Level - Term: 3 - II'),
        ('4-I', 'Level - Term: 4 - I'),
        ('4-II', 'Level - Term: 4 - II'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('CSE', 'Computer Science & Engineering'),
        ('EEE', 'Electrical & Electronic Engineering'),
        ('CE', 'Civil Engineering'),
        ('DBA', 'Business Administration'),
        ('LAW', 'Law'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES, default='CSE')
    course = models.CharField(max_length=20, choices=COURSE_CHOICES)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    file = models.FileField(upload_to='academic_resources/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} - {self.course} ({self.semester})"

    class Meta:
        ordering = ['-uploaded_at']


class ItemPost(models.Model):
    CATEGORY_CHOICES = [
        ('Books', 'Books'),
        ('Lab Tools', 'Lab Tools'),
        ('Accessories', 'Accessories'),
        ('Others', 'Others'),
    ]

    CONDITION_CHOICES = [
        ('Like New', 'Like New'),
        ('Good', 'Good'),
        ('Used', 'Used'),
    ]

    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    description = models.TextField()
    image = models.ImageField(upload_to='item_images/')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Review(models.Model):
    DEPARTMENT_CHOICES = [
        ('CSE', 'CSE'),
        ('EEE', 'EEE'),
        ('LAW', 'LAW'),
        ('CE', 'CE'),
        ('ENGLISH', 'English'),
    ]
    LEVEL_TERM_CHOICES = [
        ('1-I', 'Level-1 Term-I'),
        ('1-II', 'Level-1 Term-II'),
        ('2-I', 'Level-2 Term-I'),
        ('2-II', 'Level-2 Term-II'),
        ('3-I', 'Level-3 Term-I'),
        ('3-II', 'Level-3 Term-II'),
        ('4-I', 'Level-4 Term-I'),
        ('4-II', 'Level-4 Term-II'),
    ]
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, null=True, blank=True)
    level_term = models.CharField(max_length=10, choices=LEVEL_TERM_CHOICES, null=True, blank=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.department} - {self.level_term}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    item = models.ForeignKey(ItemPost, on_delete=models.CASCADE, related_name='bookings')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_made')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_received')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, help_text="Optional message to the seller")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['item', 'buyer']  # Prevent multiple bookings from same buyer
    
    def __str__(self):
        return f"{self.buyer.username} booked {self.item.title}"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_accepted(self):
        return self.status == 'accepted'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_cancelled(self):
        return self.status == 'cancelled'


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    item = models.ForeignKey(ItemPost, related_name='messages', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} about {self.item.title if self.item else 'General'}"

    @property
    def is_recent(self):
        """Check if message is from last 24 hours"""
        from django.utils import timezone
        from datetime import timedelta
        return self.timestamp > timezone.now() - timedelta(days=1)
    


class EmailOTPVerification(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=3)

    def __str__(self):
        return f"{self.email} - {self.otp}"    