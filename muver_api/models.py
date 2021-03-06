import datetime
import os
import stripe
from django.contrib.gis.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework.authtoken.models import Token
from twilio import TwilioRestException
from twilio.rest import TwilioRestClient


class UserProfile(models.Model):
    user = models.OneToOneField(User, null=True, blank=True,
                                related_name="profile")
    mover = models.BooleanField(default=False)
    stripe_account_id = models.CharField(max_length=24, null=True, blank=True)
    customer_id = models.CharField(max_length=24, null=True, blank=True)
    in_progress = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)
    display_name = models.CharField(max_length=50, default=None, null=True,
                                    blank=True)
    phone_number = models.CharField(max_length=10, default=None, null=True,
                                    blank=True)
    _demo_user_reset = models.BooleanField(default=False)

    def demo_reset(self):
        """
        used to reset the demo users
        """
        self.in_progress = False
        for job in self.user.jobs.all():
            # job.mover_profile.in_progress = False
            # job.mover_profile.save()
            job.delete()
        self._demo_user_reset = False
        self.save()

    def ban_user(self):
        """
        sets user to inactive
        called after mover gets a strike on his profile
        """
        self.banned = True
        self.in_progress = False
        self.user.is_active = False
        self.save()
        self.user.save()

    def unban_user(self):
        """
        used in the unban_movers command
        a scheduled command to unban users
        """
        self.banned = False
        self.user.is_active = True
        self.save()
        self.user.save()

    def __str__(self):
        return self.user.username


class Job(models.Model):
    title = models.CharField(max_length=65)
    pickup_for = models.CharField(max_length=30, null=True, blank=True)
    description = models.CharField(max_length=300, null=True, blank=True)
    user = models.ForeignKey(User, related_name="jobs")
    phone_number = models.CharField(max_length=10, null=True, blank=True)
    price = models.IntegerField()
    charge_id = models.CharField(max_length=60, null=True, blank=True)
    mover_profile = models.ForeignKey(UserProfile, null=True, blank=True)
    complete = models.BooleanField(default=False)
    conflict = models.BooleanField(default=False)
    image_url = models.URLField(null=True, blank=True)
    destination_a = models.CharField(max_length=80)
    destination_b = models.CharField(max_length=80)
    point_a = models.PointField(null=True, blank=True)
    point_b = models.PointField(null=True, blank=True)
    trip_distance = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(auto_now=True)
    confirmation_user = models.BooleanField(default=False)
    confirmation_mover = models.BooleanField(default=False)
    report_user = models.BooleanField(default=False)
    strike_mover = models.BooleanField(default=False)
    repost = models.BooleanField(default=False)
    status = models.CharField(max_length=80, null=True, blank=True)
    time_accepted = models.DateTimeField(null=True, blank=True)

    def job_posted(self):
        """
        Called when job is posted.
        Changes the job status
        and user who posted job to in_progress
        """
        self.status = "Job needs a mover."
        self.user.profile.in_progress = True
        self.user.profile.save()
        self.save()

    def in_progress(self):
        """
        Called when mover accepts job.
        Changes the job status and mover to in_progress.
        A twilio message is also sent to the user who posted the job.
        The mover profile is set to that job.
        """
        self.status = "Mover accepted job."
        self.mover_profile.in_progress = True
        time = timezone.now()
        self.time_accepted = time
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']

        client = TwilioRestClient(account_sid, auth_token)

        try:
            message = client.messages.create(body="A mover accepted your job. "
                                                  "{}: {}"
                                             .format(self.mover_profile.display_name,
                                                     self.mover_profile.phone_number),
                                             to="+18056376389", # self.phone_number
                                             from_="+17024661420")
        except TwilioRestException as e:
            print(e)
        self.mover_profile.save()
        self.save()

    def time_check(self):
        """
        returns true if the job is older than an hour
        Going to be used for a delay on when users can
        report/complete a job to prevent instantly completing/reporting.
        """
        hour_old = self.time_accepted + datetime.timedelta(hours=1)
        if timezone.now() > hour_old:
            return True
        else:
            return False

    def minutes_left(self):
        """
        returns minutes left til the job is an hour old
        """
        hour_old = self.time_accepted + datetime.timedelta(hours=1)
        time_left = hour_old - timezone.now()
        seconds = time_left.total_seconds()
        minutes = (seconds % 3600) // 60
        return minutes

    def job_conflict(self):
        """
        Used when a user or mover is reported.
        Job status changes, user and mover taken off being in_progress.
        """
        self.status = "A conflict occurred with user/mover."
        self.conflict = True
        self.user.profile.in_progress = False
        self.user.profile.save()
        self.mover_profile.in_progress = False
        self.mover_profile.save()
        self.save()

    def mover_finished(self):
        """
        Used when the mover says the job is complete.
        Changes the job status depending if the user
        has already confirmed. If user who posted already
        confirmed job is set to complete and stripe charge
        is captured/processed and sent to the mover's account
        id.
        Mover is no longer in_progress and can look for more jobs.
        """
        if not self.confirmation_user:
            self.status = "Mover set the job to complete. " \
                          "Waiting for user confirmation."
        else:
            self.status = "Job complete."
            charge = stripe.Charge.retrieve(self.charge_id)
            fee = int(charge.amount * 0.20)
            charge.capture(application_fee=fee)
            self.complete = True
            self.save()
        self.confirmation_mover = True
        self.mover_profile.in_progress = False
        self.mover_profile.save()
        self.save()

    def user_finished(self):
        """
        Called when user who posted job hits job complete.
        If Mover already said the job is complete,
        Stripe charge processed and job set to complete.
        """
        if not self.confirmation_mover:
            self.status = "User set the job to complete. " \
                          "Waiting for mover confirmation."
        else:
            self.status = "Job complete."
            self.complete = True
            charge = stripe.Charge.retrieve(self.charge_id)
            fee = int(charge.amount * 0.20)
            charge.capture(application_fee=fee)
            self.complete = True
            self.save()
        self.confirmation_user = True
        self.user.profile.in_progress = False
        self.user.profile.save()
        self.save()

    def __str__(self):
        return self.title

    def job_complete(self):

        self.status = "Job complete."
        self.complete = True
        self.save()
    # def capture_charge(self):
    #     stripe.api_key = settings.STRIPE_SECRET_KEY
    #     charge = stripe.Charge.retrieve(self.charge_id)
    #     mover = UserProfile.objects.get(pk=self.mover_profile.id)
    #     charge.destination = mover.stripe_account_id
    #     charge.application_fee = charge.amount * 0.20
    #     self.complete = True
    #     charge.capture()
    #     return charge


class Strike(models.Model):
    user = models.ForeignKey(User, related_name="strikes")
    job = models.ForeignKey(Job, related_name="strikes")
    profile = models.ForeignKey(UserProfile, related_name="strikes")
    comment = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return "Strike on {} from {}".format(self.profile, self.user)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
        UserProfile.objects.create(user=instance)

