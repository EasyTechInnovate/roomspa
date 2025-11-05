from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from User.permissions import IsTherapist
from .models import TherapistAddress, Services, BankDetails, TherapistStatus
from .serializers import TherapistAddressSerializer, ServicesSerializer, BankDetailsSerializer, TherapistStatusSerializer

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsTherapist])
def location_view(request):
    if request.method == 'GET':
        location = get_object_or_404(TherapistAddress, user=request.user)
        serializer = TherapistAddressSerializer(location)
        return Response(serializer.data)

    if request.method in ['POST', 'PUT']:
        instance = TherapistAddress.objects.filter(user=request.user).first()
        serializer = TherapistAddressSerializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save(user=request.user)

            ts, created = TherapistStatus.objects.get_or_create(user=request.user)
            ts.status = 'available'
            ts.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED if not instance else status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsTherapist])
def services_view(request):
    if request.method == 'GET':
        services = get_object_or_404(Services, user=request.user)
        serializer = ServicesSerializer(services)
        return Response(serializer.data)
    if request.method in ['POST', 'PUT']:
        instance = Services.objects.filter(user=request.user).first()
        serializer = ServicesSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED if not instance else status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsTherapist])
def bank_details_list(request):
    if request.method == 'GET':
        qs = BankDetails.objects.filter(user=request.user)
        serializer = BankDetailsSerializer(qs, many=True)
        return Response(serializer.data)
    serializer = BankDetailsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsTherapist])
def bank_details_detail(request, pk):
    instance = get_object_or_404(BankDetails, pk=pk, user=request.user)
    if request.method == 'GET':
        serializer = BankDetailsSerializer(instance)
        return Response(serializer.data)
    if request.method == 'PUT':
        serializer = BankDetailsSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    instance.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['PATCH'])
@permission_classes([IsTherapist])
def update_therapist_status(request):
    ts = request.user.therapist_status
    serializer = TherapistStatusSerializer(ts, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)