from django.contrib import admin
from muver_api.models import UserProfile, Job, Strike


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'display_name', 'phone_number',
                    'in_progress', 'mover', 'banned', 'customer_id',
                    'stripe_account_id')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'pickup_for', 'price',
                    'complete', 'conflict', 'destination_a', 'destination_b',
                    'trip_distance', 'phone_number', 'charge_id',
                    'mover_profile', 'time_accepted', 'image_url',
                    'created_at', 'modified_at', 'status',
                    'confirmation_user', 'confirmation_mover')


@admin.register(Strike)
class StrikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'profile', 'job', 'comment', 'created_at')
