import time

import geocoder
import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import GEOSGeometry
from muver_api.models import UserProfile, Job
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):

    profile = serializers.PrimaryKeyRelatedField(read_only=True)
    password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'profile', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = "__all__"


class JobSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)
    price = serializers.IntegerField()
    title = serializers.CharField(max_length=65)
    description = serializers.CharField(max_length=300,
                                        required=False,
                                        default=None)
    # save_billing = serializers.BooleanField(default=False)
    destination_a = serializers.CharField(max_length=80)
    destination_b = serializers.CharField(max_length=80)
    distance = serializers.CharField(max_length=20, required=False,
                                     read_only=True)
    phone_number = serializers.CharField(max_length=10)
    image_url = serializers.URLField(required=False,
                                     default=None,
                                     allow_blank=True,
                                     allow_null=True)

    def create(self, validated_data):

        price = validated_data['price']
        user = validated_data['user']
        title = validated_data['title']
        description = validated_data['description']
        phone_number = validated_data['phone_number']
        destination_a = validated_data['destination_a']
        destination_b = validated_data['destination_b']
        image_url = validated_data['image_url']

        ga = geocoder.google(destination_a)
        gb = geocoder.google(destination_b)
        a_lat = ga.latlng[0]
        a_lng = ga.latlng[1]
        b_lat = gb.latlng[0]
        b_lng = gb.latlng[1]
        point_a = GEOSGeometry('POINT(' + str(a_lng) + ' ' + str(a_lat) + ')',
                               srid=4326)
        point_b = GEOSGeometry('POINT(' + str(b_lng) + ' ' + str(b_lat) + ')',
                               srid=4326)

        distance = int(point_a.distance(point_b) * 100 * 0.62137)

        job = Job.objects.create(user=user,
                                 price=price,
                                 title=title,
                                 description=description,
                                 image_url=image_url,
                                 phone_number=phone_number,
                                 destination_a=destination_a,
                                 destination_b=destination_b,
                                 distance=distance
                                 )
        user.profile.in_progress = True
        user.profile.save()
        return job

    def update(self, instance, validated_data):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        instance.mover_profile = validated_data.get(
            'mover_profile', instance.mover_profile)


        if validated_data.get('mover_profile', instance.mover_profile)\
                and not instance.charge_id:
            customer = instance.user.profile.customer_id
            mover = UserProfile.objects.get(pk=instance.mover_profile.id)
            charge = stripe.Charge.create(
                amount=instance.price * 100,
                currency="usd",
                customer=customer,
                destination=mover.stripe_account_id,
                capture=False,
            )

            instance.charge_id = charge['id']
            mover.in_progress = True
            mover.save()
            instance.save()

        mover = UserProfile.objects.get(pk=instance.mover_profile.id)

        instance.confirmation_mover = validated_data.get(
            'confirmation_mover', instance.confirmation_mover)
        instance.confirmation_user = validated_data.get(
            'confirmation_user', instance.confirmation_user)

        if validated_data.get('confirmation_user', instance.confirmation_user)\
                and instance.user.profile.in_progress:
            instance.user.profile.in_progress = False
            instance.user.profile.save()

        if validated_data.get('confirmation_mover', instance.confirmation_mover) \
                and mover.in_progress:
            mover.in_progress = False
            mover.save()

        if validated_data.get('confirmation_user', instance.confirmation_user)\
                and validated_data.get('confirmation_mover',
                                       instance.confirmation_mover):

            charge = stripe.Charge.retrieve(instance.charge_id)
            fee = int(charge.amount * 0.20)
            charge.capture(application_fee=fee)
            instance.complete = True

            instance.save()
            return instance

        return super().update(instance, validated_data)

    class Meta:
        model = Job
        fields = "__all__"


class CustomerSerializer(serializers.Serializer):

    token = serializers.CharField(max_length=60)

    def create(self, validated_data):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        user = validated_data['user']
        token = validated_data['token']

        try:
            if not user.profile.customer_id:
                customer = stripe.Customer.create(
                    source=token,
                    description="mUver customer"
                )
                user.profile.customer_id = customer['id']
                user.profile.save()
                return user.profile.customer_id

            else:
                return user.profile.customer_id

        except stripe.error.CardError as e:
            pass

    def update(self, instance, validated_data):
        pass


# class ChargeSerializer(serializers.Serializer):
#
#     token = serializers.CharField(max_length=60)
#     amount = serializers.IntegerField()
#     title = serializers.CharField(max_length=65)
#     description = serializers.CharField(max_length=300,
#                                         required=False,
#                                         default=None)
#     save_billing = serializers.BooleanField(default=False)
#     destination_a = serializers.CharField(max_length=80)
#     destination_b = serializers.CharField(max_length=80)
#     distance = serializers.CharField(max_length=10)
#     phone_number = serializers.CharField(max_length=10)
#
#     def create(self, validated_data):
#         stripe.api_key = settings.STRIPE_SECRET_KEY
#         amount = validated_data['amount']
#         user = validated_data['user']
#         title = validated_data['title']
#         description = validated_data['description']
#         phone_number = validated_data['phone_number']
#         destination_a = validated_data['destination_a']
#         destination_b = validated_data['destination_b']
#         distance = validated_data['distance']
#         token = validated_data['token']
#
#         try:
#             # if save:
#
#             customer = stripe.Customer.create(
#                 source=token,
#                 description="mUver customer"
#             )
#             user.profile.customer_id = customer['id']
#             user.profile.save()
#
#             # charge = stripe.Charge.create(
#             #     amount=amount * 100,
#             #     currency="usd",
#             #     customer=customer['id'],
#             #     capture=False
#             # )
#             # price = charge['amount'] / 100
#             job = Job.objects.create(user=user,
#                                      price=amount,
#                                      title=title,
#                                      description=description,
#                                      phone_number=phone_number,
#                                      destination_a=destination_a,
#                                      destination_b=destination_b,
#                                      distance=distance
#                                      )
#             return job
#             # else:
#             #     charge = stripe.Charge.create(
#             #         amount=amount * 100,
#             #         currency='usd',
#             #         source=token,
#             #         description="Charge for mUver job",
#             #         capture=False,
#             #     )
#             #     price = charge['amount'] / 100
#             #     job = Job.objects.create(user=user,
#             #                              price=price,
#             #                              charge_id=charge['id'],
#             #                              title=title,
#             #                              description=description,
#             #                              phone_number=phone_number,
#             #                              destination_a=destination_a,
#             #                              destination_b=destination_b,
#             #                              distance=distance
#             #                              )
#             #     return job
#         except stripe.error.CardError as e:
#             pass
#
#     def update(self, instance, validated_data):
#         pass


class StripeAccountSerializer(serializers.Serializer):

    country = serializers.CharField(max_length=4, default='US')
    currency = serializers.CharField(max_length=5, default='usd')
    account_number = serializers.CharField(max_length=17)
    routing_number = serializers.CharField(max_length=9)
    first_name = serializers.CharField(max_length=35)
    last_name = serializers.CharField(max_length=35)
    dob_month = serializers.IntegerField(max_value=12)
    dob_day = serializers.IntegerField(max_value=31)
    dob_year = serializers.IntegerField()
    address_line_one = serializers.CharField(max_length=40)
    address_line_two = serializers.CharField(max_length=40,
                                             allow_null=True, allow_blank=True,
                                             default=None)
    address_city = serializers.CharField(max_length=40)
    address_state = serializers.CharField(max_length=2)
    postal_code = serializers.CharField(max_length=10)
    ssn_last_four = serializers.IntegerField(max_value=9999)

    def create(self, validated_data):

        stripe.api_key = settings.STRIPE_SECRET_KEY
        country = validated_data['country']
        currency = validated_data['currency']
        account_number = validated_data['account_number']
        routing_number = validated_data['routing_number']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        dob_month = validated_data['dob_month']
        dob_day = validated_data['dob_day']
        dob_year = validated_data['dob_year']
        address_line_one = validated_data['address_line_one']
        address_line_two = validated_data['address_line_two']
        address_city = validated_data['address_city']
        address_state = validated_data['address_state']
        postal_code = validated_data['postal_code']
        ssn_last_four = validated_data['ssn_last_four']



        try:
            account = stripe.Account.create(
                country=country,
                managed=True,
            )
            account.tos_acceptance.date = int(time.time())
            account.tos_acceptance.ip = '24.234.237.43'
            account.save()

            account.legal_entity.first_name = first_name
            account.legal_entity.last_name = last_name
            account.legal_entity.dob.month = dob_month
            account.legal_entity.dob.day = dob_day
            account.legal_entity.dob.year = dob_year
            account.legal_entity.type = "individual"

            bank_info_dict = {"object": "bank_account", "country": country,
                              "currency": currency,
                              "routing_number": routing_number,
                              "account_number": account_number}

            account.external_accounts.create(external_account=bank_info_dict)

            account.legal_entity.address.line1 = address_line_one
            if address_line_two:
                account.legal_entity.address.line2 = address_line_two
            account.legal_entity.address.postal_code = postal_code
            account.legal_entity.address.city = address_city
            account.legal_entity.address.state = address_state
            account.legal_entity.ssn_last_4 = ssn_last_four
            account.save()

            user = validated_data['user']
            user.profile.stripe_account_id = account['id']
            user.profile.mover = True
            user.profile.save()


            return account

        except stripe.error.InvalidRequestError as e:
            pass

    def update(self, instance, validated_data):
        pass

# class CaptureChargeSerializer(serializers.Serializer):
#
#     charge_id = serializers.CharField(max_length=60)
#
#     def create(self, validated_data):
#         stripe.api_key = settings.STRIPE_SECRET_KEY
#         charge = stripe.Charge.retrieve(validated_data['charge_id'])
#         charge.capture()
