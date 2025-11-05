from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from User.permissions import IsCustomer
from .models import CustomerAddress
from .serializers import CustomerAddressSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsCustomer])
def customer_address_list(request):
    if request.method == 'GET':
        qs = CustomerAddress.objects.filter(user=request.user)
        serializer = CustomerAddressSerializer(qs, many=True)
        return Response(serializer.data)
    serializer = CustomerAddressSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsCustomer])
def customer_address_detail(request, pk):
    instance = get_object_or_404(CustomerAddress, pk=pk, user=request.user)
    if request.method == 'GET':
        serializer = CustomerAddressSerializer(instance)
        return Response(serializer.data)
    if request.method == 'PUT':
        serializer = CustomerAddressSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    instance.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)