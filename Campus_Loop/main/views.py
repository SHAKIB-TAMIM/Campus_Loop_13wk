from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login , logout
from django.contrib.auth import logout
from .forms import SignUpForm, LoginForm, BookingForm, UserProfileUpdateForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from .models import Post, ItemPost, Review, AcademicResource, Booking, Message
from django.contrib import messages
from .forms import ContactForm
from .models import ContactMessage
from .models import ItemPost
from .forms import ItemPostForm
from django.http import JsonResponse
from django.db.models import Q
from.models import Review
from.forms import ReviewForm
from .models import AcademicResource
from .forms import AcademicResourceForm
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.core.mail import send_mail
from django.contrib import messages
from django.utils import timezone
from .models import EmailOTPVerification
import random
from django.core.files.base import ContentFile
from .forms import SignUpForm
import base64
from django.core.files import File
from .utils import generate_otp
from django.core.mail import send_mail
from django.conf import settings
import os




def home_view(request):
    return render(request, 'main/home.html')

def generate_otp():
    return str(random.randint(100000, 999999))


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = generate_otp()

            # Save OTP in DB
            EmailOTPVerification.objects.update_or_create(
                email=email,
                defaults={'otp': otp, 'created_at': timezone.now()}
            )

            # Save safe user data in session
            request.session['signup_data'] = {
                'username': form.cleaned_data['username'],
                'first_name': form.cleaned_data['first_name'],
                'email': email,
                'password1': form.cleaned_data['password1'],
            }

            # Save uploaded ID card temporarily
            id_card_file = request.FILES.get('id_card')
            if id_card_file:
                temp_path = f"temp_id_cards/{id_card_file.name}"
                temp_full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
                os.makedirs(os.path.dirname(temp_full_path), exist_ok=True)
                with open(temp_full_path, 'wb+') as dest:
                    for chunk in id_card_file.chunks():
                        dest.write(chunk)
                request.session['temp_id_card_path'] = temp_path

            request.session['otp_email'] = email

            send_mail(
                subject='Your OTP for Registration',
                message=f'Your OTP is: {otp}\nIt will expire in 3 minutes.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False
            )

            return redirect('verify_otp')
        else:
            print(form.errors)
    else:
        form = SignUpForm()
    return render(request, 'main/signup.html', {'form': form})

def verify_otp_view(request):
    email = request.session.get('otp_email')
    signup_data = request.session.get('signup_data')
    temp_path = request.session.get('temp_id_card_path')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        try:
            otp_entry = EmailOTPVerification.objects.get(email=email)
        except EmailOTPVerification.DoesNotExist:
            messages.error(request, "⚠️ OTP session expired. Please sign up again.")
            return redirect('signup')

        # Validate OTP and check expiry (within 180 seconds)
        if entered_otp == otp_entry.otp and (timezone.now() - otp_entry.created_at).total_seconds() <= 180:
            try:
                # Create user
                user = User.objects.create_user(
                    username=signup_data['username'],
                    email=signup_data['email'],
                    password=signup_data['password1'],
                    first_name=signup_data['first_name'],
                    is_active=True,
                )

                # Attach ID card
                if temp_path:
                    with open(os.path.join(settings.MEDIA_ROOT, temp_path), 'rb') as f:
                        django_file = File(f)
                        profile = user.profile
                        profile.id_card.save(os.path.basename(temp_path), django_file, save=True)
                    os.remove(os.path.join(settings.MEDIA_ROOT, temp_path))

                # Cleanup
                otp_entry.delete()
                request.session.flush()

                # ✅ Send Welcome Email
                send_mail(
                    subject='🎉 Email Verified - Welcome to Campus Loop!',
                    message=(
                        f"Hi {user.first_name},\n\n"
                        f"Your email has been successfully verified!\n"
                        f"You can now log in and start using Campus Loop.\n\n"
                        f"Thanks,\nThe Campus Loop Team"
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False
                )

                messages.success(request, "✅ Email verified successfully! You can now log in.")
                return redirect('login')

            except Exception as e:
                messages.error(request, f"User creation failed. Please try again.\nError: {e}")
                return redirect('signup')
        else:
            messages.error(request, "❌ Invalid or expired OTP. Please try again.")

    return render(request, 'main/verify_otp.html')


def resend_otp_view(request):
    email = request.session.get('otp_email')
    if not email:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect('signup')

    otp = generate_otp()
    EmailOTPVerification.objects.update_or_create(
        email=email,
        defaults={'otp': otp, 'created_at': timezone.now()}
    )

    send_mail(
        subject='🔁 Your New OTP for Registration',
        message=f'Your new OTP is: {otp}\nIt will expire in 3 minutes.',
        from_email='youremail@gmail.com',
        recipient_list=[email],
        fail_silently=False
    )

    messages.success(request, "✅ A new OTP has been sent to your email.")
    return redirect('verify_otp')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Try to find user with that email
        try:
            from django.contrib.auth.models import User
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            messages.error(request, "Email not found.")
            return redirect('login')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Check if user is admin/staff and redirect accordingly
            if user.is_staff:
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}! Redirecting to admin dashboard.")
                return redirect('admin_dashboard')
            else:
                return redirect('feed')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('login')
    return render(request, 'main/login.html')

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import ItemPost, Review
from .forms import ReviewForm

@login_required
def feed_view(request):
    posts = ItemPost.objects.filter(is_approved=True).order_by('-created_at')
    user_name = request.user.get_full_name() or request.user.username

    # Get items by category for the feed page
    books_items = ItemPost.objects.filter(category='Books', is_approved=True).order_by('-created_at')[:4]
    lab_tools_items = ItemPost.objects.filter(category='Lab Tools', is_approved=True).order_by('-created_at')[:4]
    accessories_items = ItemPost.objects.filter(category='Accessories', is_approved=True).order_by('-created_at')[:4]
    others_items = ItemPost.objects.filter(category='Others', is_approved=True).order_by('-created_at')[:4]

    # Check if user has completed transactions (as buyer or seller)
    from .models import Booking
    
    # Check as buyer - has accepted or completed bookings
    user_as_buyer = Booking.objects.filter(
        buyer=request.user, 
        status__in=['accepted', 'completed']
    ).exists()
    
    # Check as seller - has approved bookings (accepted or completed)
    user_as_seller = Booking.objects.filter(
        seller=request.user, 
        status__in=['accepted', 'completed']
    ).exists()
    
    user_can_review = user_as_buyer or user_as_seller

    if request.method == 'POST':
        if not user_can_review:
            messages.error(request, "You need to have completed transactions to leave a review.")
        else:
            form = ReviewForm(request.POST)
            if form.is_valid():
                submitted_name = form.cleaned_data['name']
                if submitted_name != user_name:
                    messages.error(request, "Name doesn't match your account. Please use your own name.")
                else:
                    review = form.save(commit=False)
                    review.name = user_name  # Force name match just in case
                    review.save()
                    messages.success(request, "Review submitted successfully!")
                    return redirect('feed')  # Ensure 'feed' matches your URL name
    else:
        form = ReviewForm(initial={'name': user_name})
        form.fields['name'].widget.attrs['type'] = 'hidden'  # Optional: make name field read-only

    context = {
        'posts': posts, 
        'form': form,
        'books_items': books_items,
        'lab_tools_items': lab_tools_items,
        'accessories_items': accessories_items,
        'others_items': others_items,
        'user_can_review': user_can_review,
        'user_as_buyer': user_as_buyer,
        'user_as_seller': user_as_seller,
        'recent_reviews': Review.objects.all().order_by('-created_at')[:6],  # Get 6 most recent reviews
    }
    
    return render(request, 'main/feed.html', context)

 

def see_reviews(request):
    all_reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'main/review.html', {'reviews': all_reviews})





def logout_view(request):
    logout(request)
    return render(request, 'main/logout.html')


def about_view(request):
    return render(request, 'main/about_us.html')

@login_required
def post_item_view(request):
    if request.method == 'POST':
        form = ItemPostForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.is_approved = False  # Pending approval
            item.save()
            messages.success(request, 'Your item has been submitted and is pending admin approval.')
            return redirect('feed')  # Or any success page
    else:
        form = ItemPostForm()
    return render(request, 'main/post_item.html', {'form': form})

def contact_view(request):
    return render(request, 'main/contact.html')



def books_view(request):
    books_items = ItemPost.objects.filter(category='Books', is_approved=True)
    
    # Get filter parameters
    sort_by = request.GET.get('sort', 'latest')
    condition_filter = request.GET.get('condition', '')
    
    # Apply condition filter
    if condition_filter:
        books_items = books_items.filter(condition=condition_filter)
    
    # Apply sorting
    if sort_by == 'price_low':
        books_items = books_items.order_by('price')
    elif sort_by == 'price_high':
        books_items = books_items.order_by('-price')
    elif sort_by == 'condition':
        books_items = books_items.order_by('condition')
    else:  # latest
        books_items = books_items.order_by('-created_at')
    
    # Add booking status information for each item
    from .models import Booking
    for item in books_items:
        # Check if item has active bookings (pending or accepted)
        active_booking = Booking.objects.filter(
            item=item, 
            status__in=['pending', 'accepted']
        ).first()
        item.booking_status = active_booking.status if active_booking else None
        item.booked_by = active_booking.buyer if active_booking else None
    
    context = {
        'items': books_items,
        'category': 'Books',
        'category_description': 'Find textbooks, reference books, and study materials from fellow students.',
        'current_sort': sort_by,
        'current_condition': condition_filter,
        'condition_choices': [
            ('', 'All Conditions'),
            ('Like New', 'Like New'),
            ('Good', 'Good'),
            ('Fair', 'Fair'),
        ]
    }
    return render(request, 'main/books.html', context)

def resources_view(request):
    # No longer need to fetch resources since sections are removed
    context = {}
    
    return render(request, 'main/academic_resources.html', context)

def browse_lecture_notes(request):
    lecture_notes = AcademicResource.objects.filter(
        resource_type='lecture_notes', 
        is_approved=True
    ).order_by('-uploaded_at')
    
    # Filter by department if provided
    department_filter = request.GET.get('department')
    if department_filter:
        lecture_notes = lecture_notes.filter(department=department_filter)
    
    # Filter by course if provided
    course_filter = request.GET.get('course')
    if course_filter:
        lecture_notes = lecture_notes.filter(course=course_filter)
    
    # Filter by semester if provided
    semester_filter = request.GET.get('semester')
    if semester_filter:
        lecture_notes = lecture_notes.filter(semester=semester_filter)
    
    context = {
        'resources': lecture_notes,
        'resource_type': 'Lecture Notes',
        'departments': AcademicResource.DEPARTMENT_CHOICES,
        'courses': AcademicResource.COURSE_CHOICES,
        'semesters': AcademicResource.SEMESTER_CHOICES,
    }
    
    return render(request, 'main/browse_resources.html', context)

def browse_question_papers(request):
    question_papers = AcademicResource.objects.filter(
        resource_type='question_papers', 
        is_approved=True
    ).order_by('-uploaded_at')
    
    # Filter by department if provided
    department_filter = request.GET.get('department')
    if department_filter:
        question_papers = question_papers.filter(department=department_filter)
    
    # Filter by course if provided
    course_filter = request.GET.get('course')
    if course_filter:
        question_papers = question_papers.filter(course=course_filter)
    
    # Filter by semester if provided
    semester_filter = request.GET.get('semester')
    if semester_filter:
        question_papers = question_papers.filter(semester=semester_filter)
    
    context = {
        'resources': question_papers,
        'resource_type': 'Question Papers',
        'departments': AcademicResource.DEPARTMENT_CHOICES,
        'courses': AcademicResource.COURSE_CHOICES,
        'semesters': AcademicResource.SEMESTER_CHOICES,
    }
    
    return render(request, 'main/browse_resources.html', context)

def browse_study_guides(request):
    study_guides = AcademicResource.objects.filter(
        resource_type='study_guides', 
        is_approved=True
    ).order_by('-uploaded_at')
    
    # Filter by department if provided
    department_filter = request.GET.get('department')
    if department_filter:
        study_guides = study_guides.filter(department=department_filter)
    
    # Filter by course if provided
    course_filter = request.GET.get('course')
    if course_filter:
        study_guides = study_guides.filter(course=course_filter)
    
    # Filter by semester if provided
    semester_filter = request.GET.get('semester')
    if semester_filter:
        study_guides = study_guides.filter(semester=semester_filter)
    
    context = {
        'resources': study_guides,
        'resource_type': 'Study Guides',
        'departments': AcademicResource.DEPARTMENT_CHOICES,
        'courses': AcademicResource.COURSE_CHOICES,
        'semesters': AcademicResource.SEMESTER_CHOICES,
    }
    
    return render(request, 'main/browse_resources.html', context)

def download_resource(request, resource_id):
    try:
        resource = AcademicResource.objects.get(id=resource_id, is_approved=True)
        resource.download_count += 1
        resource.save()
        return redirect(resource.file.url)
    except AcademicResource.DoesNotExist:
        messages.error(request, 'Resource not found.')
        return redirect('resources')

def browse_view(request):
    query = request.GET.get('q', '')
    if query:
        items = ItemPost.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            is_approved=True
        ).order_by('-created_at')
    else:
     items = ItemPost.objects.filter(is_approved=True).order_by('-created_at')

    # Add booking status information for each item
    from .models import Booking
    for item in items:
        # Check if item has active bookings (pending or accepted)
        active_booking = Booking.objects.filter(
            item=item, 
            status__in=['pending', 'accepted']
        ).first()
        item.booking_status = active_booking.status if active_booking else None
        item.booked_by = active_booking.buyer if active_booking else None

    return render(request, 'main/browse.html', {'items': items, 'search_query': query})

def lab_tools_view(request):
    lab_tools_items = ItemPost.objects.filter(category='Lab Tools', is_approved=True)
    
    # Get filter parameters
    sort_by = request.GET.get('sort', 'latest')
    condition_filter = request.GET.get('condition', '')
    
    # Apply condition filter
    if condition_filter:
        lab_tools_items = lab_tools_items.filter(condition=condition_filter)
    
    # Apply sorting
    if sort_by == 'price_low':
        lab_tools_items = lab_tools_items.order_by('price')
    elif sort_by == 'price_high':
        lab_tools_items = lab_tools_items.order_by('-price')
    elif sort_by == 'condition':
        lab_tools_items = lab_tools_items.order_by('condition')
    else:  # latest
        lab_tools_items = lab_tools_items.order_by('-created_at')
    
    # Add booking status information for each item
    from .models import Booking
    for item in lab_tools_items:
        # Check if item has active bookings (pending or accepted)
        active_booking = Booking.objects.filter(
            item=item, 
            status__in=['pending', 'accepted']
        ).first()
        item.booking_status = active_booking.status if active_booking else None
        item.booked_by = active_booking.buyer if active_booking else None
    
    context = {
        'items': lab_tools_items,
        'category': 'Lab Tools',
        'category_description': 'Browse laboratory equipment, tools, and scientific instruments.',
        'current_sort': sort_by,
        'current_condition': condition_filter,
        'condition_choices': [
            ('', 'All Conditions'),
            ('Like New', 'Like New'),
            ('Good', 'Good'),
            ('Fair', 'Fair'),
        ]
    }
    return render(request, 'main/lab_tools.html', context)

def accessories_view(request):
    accessories_items = ItemPost.objects.filter(category='Accessories', is_approved=True)
    
    # Get filter parameters
    sort_by = request.GET.get('sort', 'latest')
    condition_filter = request.GET.get('condition', '')
    
    # Apply condition filter
    if condition_filter:
        accessories_items = accessories_items.filter(condition=condition_filter)
    
    # Apply sorting
    if sort_by == 'price_low':
        accessories_items = accessories_items.order_by('price')
    elif sort_by == 'price_high':
        accessories_items = accessories_items.order_by('-price')
    elif sort_by == 'condition':
        accessories_items = accessories_items.order_by('condition')
    else:  # latest
        accessories_items = accessories_items.order_by('-created_at')
    
    # Add booking status information for each item
    from .models import Booking
    for item in accessories_items:
        # Check if item has active bookings (pending or accepted)
        active_booking = Booking.objects.filter(
            item=item, 
            status__in=['pending', 'accepted']
        ).first()
        item.booking_status = active_booking.status if active_booking else None
        item.booked_by = active_booking.buyer if active_booking else None
    
    context = {
        'items': accessories_items,
        'category': 'Accessories',
        'category_description': 'Discover various accessories and gadgets for your academic needs.',
        'current_sort': sort_by,
        'current_condition': condition_filter,
        'condition_choices': [
            ('', 'All Conditions'),
            ('Like New', 'Like New'),
            ('Good', 'Good'),
            ('Fair', 'Fair'),
        ]
    }
    return render(request, 'main/accessories.html', context)


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save form data to DB
            ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message']
            )
            messages.success(request, "Thank you! Your message has been sent.")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'main/contact.html', {'form': form})

@login_required
def profile_view(request):
    user_posts = ItemPost.objects.filter(user=request.user).order_by('-created_at')
    user_bookings = Booking.objects.filter(buyer=request.user).order_by('-created_at')
    received_bookings = Booking.objects.filter(seller=request.user).order_by('-created_at')
    
    # Get fresh user profile data from database
    try:
        user_profile = request.user.profile
    except:
        user_profile = None
    
    profile_form = None
    password_form = None
    
    # Handle profile update form
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = UserProfileUpdateForm(request.POST, request.FILES, instance=user_profile, user=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your profile information has been updated successfully!')
                # Don't redirect, just continue to render with updated data
            else:
                # Form has errors, keep the form with errors
                pass
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Your password has been changed successfully! Please log in again.')
                logout(request)
                return redirect('login')
    
    # Initialize forms if not already set
    if profile_form is None:
        # After successful form submission, get fresh user profile data
        if request.method == 'POST' and 'update_profile' in request.POST:
            try:
                user_profile = request.user.profile
            except:
                user_profile = None
        profile_form = UserProfileUpdateForm(instance=user_profile, user=request.user)
    if password_form is None:
        password_form = PasswordChangeForm(request.user)
    
    return render(request, 'main/profile.html', {
        'user_posts': user_posts,
        'user_bookings': user_bookings,
        'received_bookings': received_bookings,
        'user_profile': user_profile,
        'profile_form': profile_form,
        'password_form': password_form
    })

@login_required
def edit_post(request, post_id):
    try:
        post = ItemPost.objects.get(id=post_id, user=request.user)
    except ItemPost.DoesNotExist:
        messages.error(request, 'Post not found or you do not have permission to edit it.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = ItemPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your post has been updated successfully.')
            return redirect('profile')
    else:
        form = ItemPostForm(instance=post)
    
    return render(request, 'main/edit_post.html', {
        'form': form,
        'post': post
    })

@login_required
def delete_post(request, post_id):
    try:
        post = ItemPost.objects.get(id=post_id, user=request.user)
    except ItemPost.DoesNotExist:
        messages.error(request, 'Post not found or you do not have permission to delete it.')
        return redirect('profile')
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Your post has been deleted successfully.')
        return redirect('profile')
    
    return render(request, 'main/delete_post.html', {
        'post': post
    })

def search_items(request):
    query = request.GET.get('q', '')
    items = ItemPost.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        is_approved=True
    )[:5]  # Limit to 5 suggestions
    results = [{
        'id': item.id,
        'title': item.title,
        'url': f'/browse/#item-{item.id}'  # URL to the item in browse page
    } for item in items]
    return JsonResponse(results, safe=False)



@login_required
def upload(request):
    if request.method == 'POST':
        form = AcademicResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.is_approved = False  # Pending approval
            resource.save()
            messages.success(request, 'Your resource has been uploaded successfully and is pending admin approval.')
            return redirect('resources')
    else:
        form = AcademicResourceForm()
    
    return render(request, 'main/upload.html', {'form': form})

@login_required
def book_item(request, item_id):
    item = get_object_or_404(ItemPost, id=item_id, is_approved=True)
    
    # Check if user is trying to book their own item
    if item.user == request.user:
        messages.error(request, "You cannot book your own item.")
        return redirect('browse')
    
    # Check if user has already booked this item
    if Booking.objects.filter(item=item, buyer=request.user).exists():
        messages.warning(request, "You have already booked this item.")
        return redirect('browse')
    
    # Check if item is already booked by another user (pending or accepted bookings)
    existing_booking = Booking.objects.filter(
        item=item, 
        status__in=['pending', 'accepted']
    ).exclude(buyer=request.user).first()
    
    if existing_booking:
        if existing_booking.status == 'pending':
            messages.error(request, f"This item is already booked by {existing_booking.buyer.get_full_name() or existing_booking.buyer.username}. Please wait for the seller to respond.")
        else:  # accepted
            messages.error(request, f"This item is already sold to {existing_booking.buyer.get_full_name() or existing_booking.buyer.username}.")
        return redirect('browse')
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.item = item
            booking.buyer = request.user
            booking.seller = item.user
            booking.save()
            messages.success(request, f"Your booking for '{item.title}' has been submitted successfully!")
            return redirect('profile')
    else:
        form = BookingForm()
    
    return render(request, 'main/book_item.html', {
        'form': form,
        'item': item
    })

@login_required
def manage_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user is the seller of this booking
    if booking.seller != request.user:
        messages.error(request, "You don't have permission to manage this booking.")
        return redirect('profile')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ['accept', 'reject', 'complete', 'cancel']:
            if action == 'accept':
                booking.status = 'accepted'
                messages.success(request, f"Booking for '{booking.item.title}' has been accepted.")
            elif action == 'reject':
                booking.status = 'rejected'
                messages.success(request, f"Booking for '{booking.item.title}' has been rejected.")
            elif action == 'complete':
                booking.status = 'completed'
                messages.success(request, f"Booking for '{booking.item.title}' has been marked as completed.")
            elif action == 'cancel':
                booking.status = 'cancelled'
                messages.success(request, f"Booking for '{booking.item.title}' has been cancelled.")
            
            booking.save()
            return redirect('profile')
    
    return render(request, 'main/manage_booking.html', {
        'booking': booking
    })

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user is the buyer of this booking
    if booking.buyer != request.user:
        messages.error(request, "You don't have permission to cancel this booking.")
        return redirect('profile')
    
    if booking.status == 'pending':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, f"Your booking for '{booking.item.title}' has been cancelled.")
    else:
        messages.error(request, "You can only cancel pending bookings.")
    
    return redirect('profile')

def category_books(request):
    """Display all items in the Books category"""
    items = ItemPost.objects.filter(
        category='Books',
        is_approved=True
    ).order_by('-created_at')
    
    context = {
        'items': items,
        'category': 'Books',
        'category_description': 'Find textbooks, reference books, and study materials from fellow students.'
    }
    return render(request, 'main/category.html', context)


def category_lab_tools(request):
    """Display all items in the Lab Tools category"""
    items = ItemPost.objects.filter(
        category='Lab Tools',
        is_approved=True
    ).order_by('-created_at')
    
    context = {
        'items': items,
        'category': 'Lab Tools',
        'category_description': 'Browse laboratory equipment, tools, and scientific instruments.'
    }
    return render(request, 'main/category.html', context)


def category_accessories(request):
    """Display all items in the Accessories category"""
    items = ItemPost.objects.filter(
        category='Accessories',
        is_approved=True
    ).order_by('-created_at')
    
    context = {
        'items': items,
        'category': 'Accessories',
        'category_description': 'Discover various accessories and gadgets for your academic needs.'
    }
    return render(request, 'main/category.html', context)


def category_others(request):
    """Display all items in the Others category"""
    items = ItemPost.objects.filter(
        category='Others',
        is_approved=True
    ).order_by('-created_at')
    
    context = {
        'items': items,
        'category': 'Others',
        'category_description': 'Explore miscellaneous items and other useful products.'
    }
    return render(request, 'main/category.html', context)

@login_required
def inbox_view(request):
    """Show all conversations for the current user"""
    # Get all unique conversations (grouped by other user and item)
    conversations = []
    
    # Get messages where user is receiver
    received_messages = Message.objects.filter(receiver=request.user).select_related('sender', 'item')
    
    # Get messages where user is sender
    sent_messages = Message.objects.filter(sender=request.user).select_related('receiver', 'item')
    
    # Create a set of unique conversation keys (other_user_id, item_id)
    conversation_keys = set()
    
    for msg in received_messages:
        key = (msg.sender.id, msg.item.id if msg.item else None)
        conversation_keys.add(key)
    
    for msg in sent_messages:
        key = (msg.receiver.id, msg.item.id if msg.item else None)
        conversation_keys.add(key)
    
    # Build conversation list with latest message for each conversation
    for user_id, item_id in conversation_keys:
        other_user = User.objects.get(id=user_id)
        item = ItemPost.objects.get(id=item_id) if item_id else None
        
        # Get the latest message in this conversation
        latest_message = Message.objects.filter(
            Q(sender=request.user, receiver=other_user, item=item) |
            Q(sender=other_user, receiver=request.user, item=item)
        ).order_by('-timestamp').first()
        
        # Count unread messages
        unread_count = Message.objects.filter(
            sender=other_user,
            receiver=request.user,
            item=item,
            is_read=False
        ).count()
        
        conversations.append({
            'other_user': other_user,
            'item': item,
            'latest_message': latest_message,
            'unread_count': unread_count,
        })
    
    # Sort conversations by latest message timestamp
    conversations.sort(key=lambda x: x['latest_message'].timestamp, reverse=True)
    
    return render(request, 'main/inbox.html', {'conversations': conversations})

@login_required
def conversation_view(request, user_id, item_id=None):
    """Show conversation between current user and another user about a specific item"""
    other_user = get_object_or_404(User, id=user_id)
    item = get_object_or_404(ItemPost, id=item_id) if item_id else None
    
    # Get all messages in this conversation
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user, item=item) |
        Q(sender=other_user, receiver=request.user, item=item)
    ).order_by('timestamp')
    
    # Mark messages from other user as read
    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        item=item,
        is_read=False
    ).update(is_read=True)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                item=item,
                content=content
            )
            return redirect('conversation', user_id=other_user.id, item_id=item.id if item else None)
    
    return render(request, 'main/conversation.html', {
        'messages': messages,
        'other_user': other_user,
        'item': item,
    })

@login_required
def send_message_view(request, user_id, item_id=None):
    """Send a message to another user about an item"""
    if request.method == 'POST':
        other_user = get_object_or_404(User, id=user_id)
        item = get_object_or_404(ItemPost, id=item_id) if item_id else None
        content = request.POST.get('content', '').strip()
        
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                item=item,
                content=content
            )
            messages.success(request, 'Message sent successfully!')
            return redirect('conversation', user_id=other_user.id, item_id=item.id if item else None)
        else:
            messages.error(request, 'Message cannot be empty.')
    
    return redirect('inbox')

@login_required
def mark_message_read(request, message_id):
    """Mark a specific message as read"""
    message = get_object_or_404(Message, id=message_id, receiver=request.user)
    message.is_read = True
    message.save()
    return JsonResponse({'status': 'success'})


def admin_dashboard(request):
    # Check if user is admin
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('home')
    
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    
    # Get current date and time
    now = timezone.now()
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    
    # User Statistics
    total_users = User.objects.count()
    new_users_week = User.objects.filter(date_joined__gte=last_week).count()
    new_users_month = User.objects.filter(date_joined__gte=last_month).count()
    
    # Item Statistics
    total_items = ItemPost.objects.count()
    approved_items = ItemPost.objects.filter(is_approved=True).count()
    pending_items = ItemPost.objects.filter(is_approved=False).count()
    items_this_week = ItemPost.objects.filter(created_at__gte=last_week).count()
    
    # Booking Statistics
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    accepted_bookings = Booking.objects.filter(status='accepted').count()
    completed_bookings = Booking.objects.filter(status='completed').count()
    
    # Academic Resource Statistics
    total_resources = AcademicResource.objects.count()
    approved_resources = AcademicResource.objects.filter(is_approved=True).count()
    pending_resources = AcademicResource.objects.filter(is_approved=False).count()
    
    # Review Statistics
    total_reviews = Review.objects.count()
    recent_reviews_count = Review.objects.filter(created_at__gte=last_week).count()
    recent_reviews = Review.objects.order_by('-created_at')[:5]
    
    # Contact Message Statistics
    total_messages = ContactMessage.objects.count()
    unread_messages = ContactMessage.objects.filter(sent_at__gte=last_week).count()
    
    # Recent Activity
    recent_items = ItemPost.objects.order_by('-created_at')[:5]
    recent_bookings = Booking.objects.order_by('-created_at')[:5]
    recent_reviews = Review.objects.order_by('-created_at')[:5]
    recent_messages = ContactMessage.objects.order_by('-sent_at')[:5]
    recent_user_messages = Message.objects.select_related('sender', 'receiver', 'item').order_by('-timestamp')[:5]

    # Pending posts for approval
    pending_posts = ItemPost.objects.filter(is_approved=False).order_by('-created_at')
    
    # Category Distribution
    category_stats = ItemPost.objects.values('category').annotate(count=Count('category'))
    
    # Department Distribution for Reviews
    department_stats = Review.objects.values('department').annotate(count=Count('department'))
    
    # Booking Status Distribution
    booking_status_stats = Booking.objects.values('status').annotate(count=Count('status'))
    
    # Pending academic resources for approval
    pending_resources_list = AcademicResource.objects.filter(is_approved=False).order_by('-uploaded_at')
    
    context = {
        # Statistics
        'total_users': total_users,
        'new_users_week': new_users_week,
        'new_users_month': new_users_month,
        'total_items': total_items,
        'approved_items': approved_items,
        'pending_items': pending_items,
        'items_this_week': items_this_week,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'accepted_bookings': accepted_bookings,
        'completed_bookings': completed_bookings,
        'total_resources': total_resources,
        'approved_resources': approved_resources,
        'pending_resources': pending_resources,
        'total_reviews': total_reviews,
        'recent_reviews_count': recent_reviews_count,
        'recent_reviews': recent_reviews,
        'total_messages': total_messages,
        'unread_messages': unread_messages,
        
        # Recent Activity
        'recent_items': recent_items,
        'recent_bookings': recent_bookings,
        'recent_reviews': recent_reviews,
        'recent_messages': recent_messages,
        'recent_user_messages': recent_user_messages,
        # Pending posts
        'pending_posts': pending_posts,
        # Pending resources
        'pending_resources_list': pending_resources_list,
        
        # Distribution Data
        'category_stats': category_stats,
        'department_stats': department_stats,
        'booking_status_stats': booking_status_stats,
        
        # Date ranges
        'last_week': last_week,
        'last_month': last_month,
    }
    
    return render(request, 'main/admin_dashboard.html', context)

@login_required
@require_POST
def admin_approve_item(request, item_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('home')
    try:
        item = ItemPost.objects.get(id=item_id)
        item.is_approved = True
        item.save()
        messages.success(request, f"Item '{item.title}' has been approved successfully!")
    except ItemPost.DoesNotExist:
        messages.error(request, "Item not found.")
    return redirect('admin_dashboard')

@login_required
@require_POST
def admin_reject_item(request, item_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('home')
    try:
        item = ItemPost.objects.get(id=item_id)
        item.delete()
        messages.success(request, f"Item '{item.title}' has been rejected and deleted.")
    except ItemPost.DoesNotExist:
        messages.error(request, "Item not found.")
    return redirect('admin_dashboard')

@login_required
@require_POST
def admin_approve_resource(request, resource_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    try:
        resource = AcademicResource.objects.get(id=resource_id)
        resource.is_approved = True
        resource.save()
        messages.success(request, f"Resource '{resource.title}' has been approved successfully!")
    except AcademicResource.DoesNotExist:
        messages.error(request, "Resource not found.")
    return redirect('admin_dashboard')

@login_required
@require_POST
def admin_reject_resource(request, resource_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    try:
        resource = AcademicResource.objects.get(id=resource_id)
        resource.delete()
        messages.success(request, f"Resource '{resource.title}' has been rejected and deleted.")
    except AcademicResource.DoesNotExist:
        messages.error(request, "Resource not found.")
    return redirect('admin_dashboard')

@login_required
def admin_delete_user(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('home')
    
    try:
        user = User.objects.get(id=user_id)
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
        else:
            username = user.username
            user.delete()
            messages.success(request, f"User '{username}' has been deleted successfully!")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    
    return redirect('admin_dashboard')

@login_required
def admin_delete_review(request, review_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    try:
        review = Review.objects.get(id=review_id)
        review.delete()
        messages.success(request, f"Review by '{review.name}' has been deleted successfully!")
    except Review.DoesNotExist:
        messages.error(request, "Review not found.")
    next_url = request.POST.get('next') or 'admin_dashboard'
    return redirect(next_url)

@login_required
def admin_delete_message(request, message_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    
    try:
        message = ContactMessage.objects.get(id=message_id)
        if request.method == 'POST':
            message_name = message.name
            message.delete()
            messages.success(request, f"Message from '{message_name}' has been deleted successfully!")
            next_url = request.POST.get('next') or 'admin_dashboard'
            return redirect(next_url)
        else:
            return render(request, 'main/admin_confirm_delete_message.html', {'message': message})
    except ContactMessage.DoesNotExist:
        messages.error(request, "Message not found.")
        return redirect('admin_dashboard')

@login_required
def admin_manage_bookings(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('home')
    
    try:
        bookings = Booking.objects.all().order_by('-created_at')
        
        if request.method == 'POST':
            booking_id = request.POST.get('booking_id')
            action = request.POST.get('action')
            
            try:
                booking = Booking.objects.get(id=booking_id)
                if action == 'accept':
                    booking.status = 'accepted'
                    messages.success(request, f"Booking for '{booking.item.title}' has been accepted.")
                elif action == 'reject':
                    booking.status = 'rejected'
                    messages.success(request, f"Booking for '{booking.item.title}' has been rejected.")
                elif action == 'complete':
                    booking.status = 'completed'
                    messages.success(request, f"Booking for '{booking.item.title}' has been marked as completed.")
                elif action == 'cancel':
                    booking.status = 'cancelled'
                    messages.success(request, f"Booking for '{booking.item.title}' has been cancelled.")
                
                booking.save()
            except Booking.DoesNotExist:
                messages.error(request, "Booking not found.")
        
        return render(request, 'main/admin_manage_bookings.html', {'bookings': bookings})
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('admin_dashboard')

@login_required
def admin_manage_booking(request, booking_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            booking.status = 'accepted'
            messages.success(request, f"Booking for '{booking.item.title}' has been accepted.")
        elif action == 'reject':
            booking.status = 'rejected'
            messages.success(request, f"Booking for '{booking.item.title}' has been rejected.")
        elif action == 'complete':
            booking.status = 'completed'
            messages.success(request, f"Booking for '{booking.item.title}' has been marked as completed.")
        elif action == 'cancel':
            booking.status = 'cancelled'
            messages.success(request, f"Booking for '{booking.item.title}' has been cancelled.")
        booking.save()
        return redirect('admin_dashboard')
    return render(request, 'main/admin_manage_booking.html', {'booking': booking})

class AdminReviewEditForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'department', 'level_term', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'level_term': forms.TextInput(attrs={'class': 'form-control'}),
        }

@login_required
def admin_edit_review(request, review_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        form = AdminReviewEditForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated successfully!")
            return redirect('admin_dashboard')
    else:
        form = AdminReviewEditForm(instance=review)
    return render(request, 'main/admin_edit_review.html', {'form': form, 'review': review})

@login_required
def admin_manage_users(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    users = User.objects.all().order_by('-last_login')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' created successfully!")
            return redirect('admin_manage_users')
    else:
        form = UserCreationForm()
    return render(request, 'main/admin_manage_users.html', {'users': users, 'form': form})

@login_required
def admin_edit_user(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_manage_users')
    user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        profile_form = UserProfileUpdateForm(request.POST, request.FILES, instance=profile, user=user)
        if profile_form.is_valid():
            # Update user fields from the form
            user.username = request.POST.get('username', user.username)
            user.is_staff = 'is_staff' in request.POST
            user.save()
            profile_form.save()
            messages.success(request, f"User '{user.username}' updated successfully!")
            return redirect('admin_manage_users')
        else:
            # Form has errors, will be displayed in template
            pass
    else:
        profile_form = UserProfileUpdateForm(instance=profile, user=user)
    return render(request, 'main/admin_edit_user.html', {'edit_user': user, 'profile_form': profile_form})

@login_required
def admin_manage_reviews(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'main/admin_manage_reviews.html', {'reviews': reviews})

@login_required
def admin_manage_items(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    items = ItemPost.objects.all().order_by('-created_at')
    return render(request, 'main/admin_manage_items.html', {'items': items})

@login_required
def admin_manage_messages(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    messages_list = ContactMessage.objects.all().order_by('-sent_at')
    return render(request, 'main/admin_manage_messages.html', {'messages': messages_list})

@login_required
def admin_bulk_delete_messages(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        message_ids = request.POST.getlist('message_ids')
        if message_ids:
            deleted_count = 0
            for message_id in message_ids:
                try:
                    message = ContactMessage.objects.get(id=message_id)
                    message.delete()
                    deleted_count += 1
                except ContactMessage.DoesNotExist:
                    continue
            
            if deleted_count > 0:
                messages.success(request, f"{deleted_count} message(s) have been deleted successfully!")
            else:
                messages.error(request, "No messages were deleted.")
        else:
            messages.error(request, "No messages were selected for deletion.")
    
    return redirect('admin_manage_messages')

@login_required
def admin_edit_item(request, item_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_manage_items')
    item = get_object_or_404(ItemPost, id=item_id)
    if request.method == 'POST':
        item.title = request.POST.get('title', item.title)
        item.category = request.POST.get('category', item.category)
        item.price = request.POST.get('price', item.price)
        item.description = request.POST.get('description', item.description)
        if 'image' in request.FILES:
            item.image = request.FILES['image']
        item.save()
        messages.success(request, f"Item '{item.title}' updated successfully!")
        return redirect('admin_manage_items')
    return render(request, 'main/admin_edit_item.html', {'item': item})

@login_required
def admin_delete_item(request, item_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_manage_items')
    item = get_object_or_404(ItemPost, id=item_id)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item deleted successfully!")
        return redirect('admin_manage_items')
    return render(request, 'main/admin_delete_item.html', {'item': item})

@login_required
def admin_conversation_view(request, user1_id, user2_id, item_id=None):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    
    # Handle message editing
    if request.method == 'POST' and 'edit_message' in request.POST:
        message_id = request.POST.get('message_id')
        new_content = request.POST.get('new_content', '').strip()
        
        if message_id and new_content:
            try:
                message = Message.objects.get(id=message_id)
                message.content = new_content
                message.save()
                messages.success(request, "Message updated successfully!")
            except Message.DoesNotExist:
                messages.error(request, "Message not found.")
        
        # Redirect back to the same conversation view
        if item_id:
            return redirect('admin_conversation_item', user1_id, user2_id, item_id)
        else:
            return redirect('admin_conversation', user1_id, user2_id)
    
    if user1_id == user2_id:
        return render(request, 'main/admin_conversation.html', {
            'messages': [],
            'user1': None,
            'user2': None,
            'item': None,
            'error': 'Cannot view conversation with only one user.'
        })
    user1 = get_object_or_404(User, id=user1_id)
    user2 = get_object_or_404(User, id=user2_id)
    item = None
    if item_id:
        try:
            item = ItemPost.objects.get(id=item_id)
        except ItemPost.DoesNotExist:
            return render(request, 'main/admin_conversation.html', {
                'messages': [],
                'user1': user1,
                'user2': user2,
                'item': None,
                'error': 'Item not found.'
            })
    if item:
        messages_qs = Message.objects.filter(
            (Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1)) & Q(item=item)
        ).order_by('timestamp')
    else:
        messages_qs = Message.objects.filter(
            (Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1)) & Q(item__isnull=True)
        ).order_by('timestamp')
    if not messages_qs.exists():
        return render(request, 'main/admin_conversation.html', {
            'messages': [],
            'user1': user1,
            'user2': user2,
            'item': item,
            'error': 'No messages found in this conversation.'
        })
    return render(request, 'main/admin_conversation.html', {
        'messages': messages_qs,
        'user1': user1,
        'user2': user2,
        'item': item,
        'error': None,
    })

@login_required
def admin_manage_user_messages(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    
    # Handle message editing
    if request.method == 'POST' and 'edit_message' in request.POST:
        message_id = request.POST.get('message_id')
        new_content = request.POST.get('new_content', '').strip()
        
        if message_id and new_content:
            try:
                message = Message.objects.get(id=message_id)
                message.content = new_content
                message.save()
                messages.success(request, "Message updated successfully!")
            except Message.DoesNotExist:
                messages.error(request, "Message not found.")
        
        return redirect('admin_manage_user_messages')
    
    messages_list = Message.objects.select_related('sender', 'receiver', 'item').order_by('-timestamp')
    return render(request, 'main/admin_manage_user_messages.html', {'messages': messages_list})

@login_required
def admin_delete_user_message(request, message_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    msg = get_object_or_404(Message, id=message_id)
    if request.method == 'POST':
        msg.delete()
        messages.success(request, "Message deleted successfully.")
        return redirect('admin_manage_user_messages')
    return render(request, 'main/admin_confirm_delete_user_message.html', {'msg': msg})

@login_required
def admin_manage_resources(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('admin_dashboard')
    resources = AcademicResource.objects.all().order_by('-uploaded_at')
    return render(request, 'main/admin_manage_resources.html', {'resources': resources})