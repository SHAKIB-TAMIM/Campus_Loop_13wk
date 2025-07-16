from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Post
from .models import ContactMessage
from .models import ItemPost
from.models import Review
from .models import AcademicResource
from .models import UserProfile
from .models import Booking
from .models import Message
from .models import EmailOTPVerification


# Unregister the original User admin
admin.site.unregister(User)

# Register it again with the default or your custom admin
admin.site.register(User, UserAdmin)
admin.site.register(Post)
admin.site.register(Review)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'created_at', 'has_id_card')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'user__first_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def has_id_card(self, obj):
        return bool(obj.id_card)
    has_id_card.boolean = True
    has_id_card.short_description = 'Has ID Card'

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'sent_at')
    list_filter = ('subject', 'sent_at')
    search_fields = ('name', 'email', 'message')

@admin.register(ItemPost)
class ItemPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'category', 'condition', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'category', 'condition')
    actions = ['approve_items']

    def approve_items(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} item(s) approved.")
    approve_items.short_description = "Approve selected items"

@admin.register(AcademicResource)
class AcademicResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'department', 'course', 'semester', 'uploaded_by', 'is_approved', 'uploaded_at')
    list_filter = ('is_approved', 'resource_type', 'department', 'course', 'semester')
    search_fields = ('title', 'description', 'uploaded_by__username')
    actions = ['approve_resources']

    def approve_resources(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} resource(s) approved.")
    approve_resources.short_description = "Approve selected resources"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('item', 'buyer', 'seller', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('item__title', 'buyer__username', 'seller__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('item', 'buyer', 'seller', 'status')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'item', 'is_read', 'timestamp')
    list_filter = ('is_read', 'timestamp', 'item__category')
    search_fields = ('sender__username', 'receiver__username', 'content', 'item__title')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Message Information', {
            'fields': ('sender', 'receiver', 'item', 'content')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'receiver', 'item')


@admin.register(EmailOTPVerification)
class EmailOTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp', 'created_at', 'is_expired_display')
    search_fields = ('email', 'otp')
    ordering = ('-created_at',)

    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Expired?'

