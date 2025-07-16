from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import ContactMessage
from .models import ItemPost
from .models import Post
from.models import Review
from .models import AcademicResource
from .models import UserProfile
from .models import Booking




class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True, label='Full Name')
    username = forms.CharField(label='username')
    id_card = forms.ImageField(
        required=True,
        label='ID Card',
        help_text='Upload a clear photo of your student ID card (JPG, PNG, PDF)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'email', 'username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter username'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter your full name'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter your email'})
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email    

    def clean_id_card(self):
        id_card = self.cleaned_data.get('id_card')
        if id_card:
            # Check file size (5MB limit)
            if id_card.size > 5 * 1024 * 1024:
                raise forms.ValidationError("ID card file size must be under 5MB.")
            
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
            file_extension = '.' + id_card.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError("Please upload a valid file type (JPG, PNG, PDF).")
        
        return id_card

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Create or update user profile with ID card
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
            
            if self.cleaned_data.get('id_card'):
                profile.id_card = self.cleaned_data['id_card']
                profile.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Student ID')



class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your email address'
    }))
    subject = forms.ChoiceField(choices=[
        ('General Inquiry', 'General Inquiry'),
        ('Support', 'Support'),
        ('Feedback', 'Feedback'),
    ], widget=forms.Select(attrs={'class': 'form-select'}))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 5,
        'placeholder': 'Your message'
    }))


class ItemPostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove 'Others' from category choices
        self.fields['category'].choices = [
            (value, label) for value, label in self.fields['category'].choices if value != 'Others'
        ]

    class Meta:
        model = ItemPost
        fields = ['title', 'price', 'category', 'condition', 'description', 'image']


class AcademicResourceForm(forms.ModelForm):
    class Meta:
        model = AcademicResource
        fields = ['title', 'description', 'resource_type', 'department', 'course', 'semester', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. Calculus II - Integration Techniques'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add details about these notes (e.g., topics covered, key concepts)'
            }),
            'resource_type': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'course': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'semester': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.txt,.jpg,.png'
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 10MB.")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.jpg', '.jpeg', '.png']
            file_extension = '.' + file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError("Please upload a valid file type (PDF, DOC, DOCX, PPT, PPTX, TXT, JPG, PNG).")
        
        return file


class ReviewForm(forms.ModelForm):
    department = forms.ChoiceField(
        choices=[
            ('CSE', 'CSE'),
            ('EEE', 'EEE'),
            ('LAW', 'LAW'),
            ('CE', 'CE'),
            ('ENGLISH', 'English'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='CSE',
        required=True
    )
    level_term = forms.ChoiceField(
        choices=[
            ('1-I', 'Level-1 Term-I'),
            ('1-II', 'Level-1 Term-II'),
            ('2-I', 'Level-2 Term-I'),
            ('2-II', 'Level-2 Term-II'),
            ('3-I', 'Level-3 Term-I'),
            ('3-II', 'Level-3 Term-II'),
            ('4-I', 'Level-4 Term-I'),
            ('4-II', 'Level-4 Term-II'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='1-II',
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].initial = 'CSE'
        self.fields['level_term'].initial = '1-II'

    class Meta:
        model = Review
        fields = ['name', 'department', 'level_term', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review...'
            }),
        }

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write a message to the seller....'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].required = False


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True, label='First Name')
    last_name = forms.CharField(max_length=100, required=True, label='Last Name')
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False, label='Phone Number')
    university = forms.CharField(max_length=200, required=False, label='University')
    department = forms.CharField(max_length=100, required=False, label='Department/Major')
    
    class Meta:
        model = UserProfile
        fields = ['id_card']
        widgets = {
            'id_card': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            
            # Set initial values from UserProfile if it exists
            try:
                profile = user.profile
                self.fields['phone_number'].initial = profile.phone_number
                self.fields['university'].initial = profile.university
                self.fields['department'].initial = profile.department
            except:
                pass
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_id_card(self):
        id_card = self.cleaned_data.get('id_card')
        if id_card:
            # Check file size (5MB limit)
            if id_card.size > 5 * 1024 * 1024:
                raise forms.ValidationError("ID card file size must be under 5MB.")
            
            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
            file_extension = '.' + id_card.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError("Please upload a valid file type (JPG, PNG, PDF).")
        
        return id_card
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update user information
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()
        
        # Update UserProfile information
        profile.phone_number = self.cleaned_data.get('phone_number', '')
        profile.university = self.cleaned_data.get('university', '')
        profile.department = self.cleaned_data.get('department', '')
        
        if commit:
            profile.save()
        
        return profile

class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password'
        }),
        label='Current Password'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        label='New Password'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        label='Confirm New Password'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError('Current password is incorrect.')
        return current_password
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('New passwords do not match.')
            
            # Check password strength
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
        
        return password2
    
    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user
