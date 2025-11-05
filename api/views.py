import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from User.permissions import IsTherapist, IsCustomer
from User.functions.image_handler import upload_image
from .models import Pictures
from .serializers import PicturesSerializer

def handle_uploaded_file(file, subfolder):
    upload_dir = os.path.join(settings.MEDIA_ROOT, subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.name)
    with open(file_path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return upload_image(file_path, f"pictures/{subfolder}")

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsTherapist | IsCustomer])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def pictures_view(request):
    if request.method == 'GET':
        pictures = get_object_or_404(Pictures, user=request.user)
        serializer = PicturesSerializer(pictures)
        return Response(serializer.data)
    
    if request.method == 'POST':
        uploaded = {}
        if 'profile_picture' in request.FILES:
            url = handle_uploaded_file(request.FILES['profile_picture'], "profile")
            if url:
                uploaded['profile_picture'] = url
                
        if request.user.role == 'therapist':
            if 'certificate' in request.FILES:
                url = handle_uploaded_file(request.FILES['certificate'], "certificates")
                if url:
                    uploaded['certificate'] = url
                    
            if 'national_id' in request.FILES:
                url = handle_uploaded_file(request.FILES['national_id'], "documents")
                if url:
                    uploaded['national_id'] = url
                    
        if 'more_pictures' in request.FILES:
            more_urls = []
            for pic in request.FILES.getlist('more_pictures'):
                url = handle_uploaded_file(pic, "additional")
                if url:
                    more_urls.append(url)
            if more_urls:
                uploaded['more_pictures'] = more_urls
                
        pictures = Pictures.objects.filter(user=request.user).first()
        if pictures:
            if 'profile_picture' in uploaded:
                pictures.profile_picture = uploaded['profile_picture']
            if 'certificate' in uploaded and request.user.role == 'therapist':
                pictures.certificate = uploaded['certificate']
            if 'national_id' in uploaded and request.user.role == 'therapist':
                pictures.national_id = uploaded['national_id']
            if 'more_pictures' in uploaded:
                if len(pictures.more_pictures) >= 6 or len(pictures.more_pictures) + len(uploaded['more_pictures']) > 6:
                    return Response({"error": "Exceeded maximum limit of 6 images"}, status=status.HTTP_400_BAD_REQUEST)
                pictures.more_pictures.extend(uploaded['more_pictures'])
            pictures.save()
        else:
            required = ['profile_picture']
            if request.user.role == 'therapist':
                required.extend(['certificate', 'national_id'])
                
            for field in required:
                if field not in uploaded and field not in request.data:
                    return Response({"error": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
                    
            data = {'user': request.user, **uploaded}
            for field in required:
                if field not in uploaded and field in request.data:
                    data[field] = request.data[field]
                    
            if 'more_pictures' not in uploaded and 'more_pictures' in request.data:
                data['more_pictures'] = request.data['more_pictures'] if isinstance(request.data['more_pictures'], list) else []
                
            pictures = Pictures.objects.create(**data)
            
        serializer = PicturesSerializer(pictures)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    if request.method == 'DELETE':
        url = request.data.get('url')
        if not url:
            return Response({"error": "Image URL is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        pictures = get_object_or_404(Pictures, user=request.user)
        if url in pictures.more_pictures:
            pictures.more_pictures.remove(url)
            pictures.save()
            return Response({"message": "Image deleted", "more_pictures": pictures.more_pictures})
            
        return Response({"error": "Image URL not found"}, status=status.HTTP_404_NOT_FOUND)