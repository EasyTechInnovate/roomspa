from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import UserProfile
from .serializers import UserProfileUpdateSerializer
from .functions.generate_verification import generate_verification_token
from .functions.generate_otp import generate_verification_otp
from .functions.send_mail import send_registration_link, send_phone_verification
from .functions.encryption import encrypt_password
from datetime import datetime, timezone

from api.serializers import PicturesSerializer
from therapist.serializers import TherapistAddressSerializer
from customer.serializers import CustomerAddressSerializer
from api.models import Pictures
from therapist.models import TherapistAddress
from customer.models import  CustomerAddress

@api_view(['GET'])
def healthCheck(request):
    now = datetime.now(timezone.utc).isoformat()
    return Response({
        "success": True,
        "status": "UP",
        "version": "1.0.0",
        "timestamp": now,
        "server_time": now,
        "message": "The API server is healthy"
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def login(request):
    identifier = request.data.get('identifier', '').strip()
    password = request.data.get('password')
    
    from django.contrib.auth import get_backends

    backend = get_backends()[0]  
    
    user = backend.authenticate(request, username=identifier, password=password)
    
    if user is not None:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        return Response({
            "message": "Login successful",
            "user": {
                "id": str(user.pk),
                "name": user.name,
                "email": user.email,
                "role": user.role
            },
            "access_token": access_token,
            "refresh_token": refresh_token
        }, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user

    try:
        pics = user.therapist_pictures
        pictures = PicturesSerializer(pics).data
    except Pictures.DoesNotExist:
        pictures = {
            "profile_picture": None,
            "more_pictures": [],
            "certificate": None,
            "national_id": None
        }

    if user.role == 'customer':
        addr_qs = user.customer_addresses.all()
        address = CustomerAddressSerializer(addr_qs, many=True).data if addr_qs.exists() else []
    elif user.role == 'therapist':
        addr = getattr(user, 'therapist_address', None)
        address = TherapistAddressSerializer(addr).data if addr else []
    else:
        address = None

    data = {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone_number": user.phone_number,
            "country_code": user.country_code,
            "number": user.number,
            "gender": user.gender,
            "role": user.role,
        },
        "status": {
            "verification_status": user.verification_status,
            "consent": user.consent,
        },
        "pictures": pictures,
        "address": address,
        "is_onboarding_required": not bool(address)
    }
    return Response(data, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()  
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'message': 'Invalid refresh token'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register(request):
    data = request.data
    name = data.get('name', '').strip()
    email = data.get('email')
    password = data.get('password')
    country_code = data.get('country_code')
    number = data.get('number')
    verification_method = data.get('verification_method')
    gender = data.get('gender', 'prefer_not_to_say')
    role = data.get('role', 'customer')
    consent = data.get('consent', False)

    if email and UserProfile.objects.filter(email=email, verification_status=True).exists():
        return Response({'message': 'Email address already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    full_phone = None
    if country_code and number:
        full_phone = f"{country_code}{number}"
        if UserProfile.objects.filter(phone_number=full_phone, verification_status=True).exists():
            return Response({'message': 'Phone number already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    verification_token = generate_verification_otp()
    if verification_method == 'email' and email:
        send_registration_link(name, email, verification_token, 'registration')
    elif verification_method == 'phone' and full_phone:
        # Use SMS for phone verification instead of email
        sms_result = send_phone_verification(name, full_phone, verification_token, 'registration')
        if not sms_result.get("success"):
            return Response({'message': f'SMS sending failed: {sms_result.get("error")}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'message': 'Invalid verification method or missing contact info.'}, status=status.HTTP_400_BAD_REQUEST)

    user_qs = None
    if email and UserProfile.objects.filter(email=email).exists():
        user_qs = UserProfile.objects.filter(email=email)
    elif full_phone and UserProfile.objects.filter(phone_number=full_phone).exists():
        user_qs = UserProfile.objects.filter(phone_number=full_phone)

    if user_qs:
        user_profile = user_qs.first()
        user_profile.name = name
        user_profile.email = email
        user_profile.country_code = country_code
        user_profile.number = number
        user_profile.gender = gender
        user_profile.role = role
        user_profile.consent = consent
        user_profile.verification_token = verification_token
        if password:
            user_profile.set_password(password)
        user_profile.save()
    else:
        UserProfile.objects.create_user(
            name=name,
            email=email,
            password=password,
            country_code=country_code,
            number=number,
            phone_number=full_phone,
            gender=gender,
            role=role,
            consent=consent,
            verification_token=verification_token
        )

    return Response({'message': 'Account created. Please verify.'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def email_verification(request):
    identifier = request.data.get('identifier', '').strip()
    verification_token = request.data.get('verification_token')

    if '@' in identifier:
        user_profile = UserProfile.objects.filter(
            email=identifier,
            verification_token=verification_token
        ).first()
    else:
        user_profile = UserProfile.objects.filter(
            phone_number=identifier,
            verification_token=verification_token
        ).first()

    
    if user_profile:
        user_profile.verification_status = True
        user_profile.verification_token = None
        user_profile.save()
        return Response({'message': 'Account verified successfully.'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def forgot_password(request):
    identifier = request.data.get('identifier', '').strip()
    method = ''
    if '@' in identifier:
        method = 'email'
        user_profile = UserProfile.objects.filter(email=identifier).first()
    else:
        user_profile = UserProfile.objects.filter(phone_number=identifier).first()
        
    if not user_profile:
        return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    verification_token = generate_verification_otp()
    user_profile.verification_token = verification_token
    user_profile.save()

    if method == 'email':
        send_registration_link(user_profile.name, user_profile.email, verification_token, "password_reset")
        return Response({'message': 'An email to reset your password has been sent.'}, status=status.HTTP_200_OK)
    else:
        # Handle phone verification - actually send SMS now
        sms_result = send_phone_verification(user_profile.name, user_profile.phone_number, verification_token, 'password_reset')
        if sms_result.get("success"):
            return Response({'message': 'An SMS to reset your password has been sent to your phone number.'},
                           status=status.HTTP_200_OK)
        else:
            return Response({'message': f'SMS sending failed: {sms_result.get("error")}'},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def reset_password(request):
    identifier = request.data.get('identifier', '').strip()
    verification_token = request.data.get('verification_token')

    if '@' in identifier:
        user_profile = UserProfile.objects.filter(
            email=identifier,
            verification_token=verification_token
        ).first()
    else:
        user_profile = UserProfile.objects.filter(
            phone_number=identifier,
            verification_token=verification_token
        ).first()
        
    if not user_profile:
        return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    new_password = request.data.get('new_password')
    
    if user_profile:
        user_profile.verification_token = None
        user_profile.set_password(new_password)
        user_profile.save()
        return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Password reset failed.'}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    user = request.user
    new_email = request.data.get("email")
    new_phone = request.data.get("phone_number")
    new_password = request.data.get("password")
    
    if new_email and new_email != user.email:
        verification_token = generate_verification_otp()
        send_registration_link(user.name, new_email, verification_token, "email_update")
        
        user.verification_token = verification_token
        user.save()
        return Response({"message": "An email to update your email has been sent."}, status=status.HTTP_202_ACCEPTED)
    
    if new_phone and new_phone != user.phone_number:
        verification_token = generate_verification_token()
        encrypted_new_phone = encrypt_password(new_phone)
        user.verification_token = verification_token
        user.save()
        
        # Handle phone verification flow
        return Response({"message": "A verification code has been sent to your new phone number."}, 
                       status=status.HTTP_202_ACCEPTED)
    
    if new_password and not user.check_password(new_password):
        encrypted_password = encrypt_password(new_password)
        reset_link = f"{settings.BASE_URL}/reset-password/?name={user.name}&verification-token={encrypted_password}"
        user.verification_token = encrypted_password
        user.save()
        
        if user.email:
            send_registration_link(user.name, user.email, reset_link, "password_reset")
        
        return Response({"message": "A verification link to update your password has been sent."}, 
                       status=status.HTTP_200_OK)
    
    serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Profile updated successfully", "data": serializer.data}, 
                       status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def update_email_phone(request):
    identifier = request.data.get('identifier', '').strip()
    verification_token = request.data.get('verification_token')
    new_identifier = request.data.get('new_identifier')

    if '@' in identifier:
        user_profile = UserProfile.objects.filter(
            email=identifier,
            verification_token=verification_token
        ).first()
        if not user_profile:
            return Response({'message': 'Email Update Failed.'}, status=status.HTTP_404_NOT_FOUND)
        user_profile.verification_token = None
        user_profile.email = new_identifier
        user_profile.save()
    else:
        user_profile = UserProfile.objects.filter(
            phone_number=identifier,
            verification_token=verification_token
        ).first()
        if not user_profile:
            return Response({'message': 'Phone Number Update Failed.'}, status=status.HTTP_404_NOT_FOUND)
        user_profile.verification_token = None
        user_profile.phone_number = new_identifier
        user_profile.save()
        
    if user_profile:
        return Response({'message': 'Update successful.'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Update failed.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_profile(request):
    user = request.user
    user.delete()
    return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def verify_token(request):
    token = request.data.get('access_token')

    if not token:
        return Response({
            "success": False,
            "message": "Token is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        UntypedToken(token)
        return Response({
            "success": True,
            "message": "Token is valid"
        }, status=status.HTTP_200_OK)
    except (TokenError, InvalidToken) as e:
        return Response({
            "success": False,
            "message": str(e)
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def refresh_token(request):
    refresh_token = request.data.get('refresh_token')

    if not refresh_token:
        return Response({
            "success": False,
            "message": "Refresh token is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        new_access_token = str(token.access_token)

        return Response({
            "success": True,
            "access_token": new_access_token,
            "message": "Access token refreshed successfully"
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "success": False,
            "message": "Invalid refresh token",
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')

    if not current_password or not new_password:
        return Response({
            "success": False,
            "message": "Current password and new password are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if current password is correct
    if not user.check_password(current_password):
        return Response({
            "success": False,
            "message": "Current password is incorrect"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Set new password
    user.set_password(new_password)
    user.save()

    return Response({
        "success": True,
        "message": "Password changed successfully"
    }, status=status.HTTP_200_OK)