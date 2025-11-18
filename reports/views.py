from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from .models import User, Department, Report, Comment
from .serializers import (
    UserSerializer,
    DepartmentSerializer,
    ReportSerializer,
    CommentSerializer
)


# =========================
#  AUTH & USER VIEWS
# =========================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def user_list_create(request):
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        data = request.data
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save(role=data.get('role', 'EMPLOYEE'))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def user_detail_update_delete(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================
#  DEPARTMENT VIEWS
# =========================

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def department_list_create(request):
    if request.method == 'GET':
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
#  REPORT VIEWS
# =========================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def report_list_create(request):
    if request.method == 'GET':
        # Admin sees all; users see only their own reports
        if request.user.role == 'ADMIN':
            reports = Report.objects.all()
        else:
            reports = Report.objects.filter(user=request.user)

        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # Auto-assign logged-in user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def report_update_delete(request, pk):
    try:
        report = Report.objects.get(pk=pk)
    except Report.DoesNotExist:
        return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        if request.user != report.user and request.user.role != 'ADMIN':
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ReportSerializer(report, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        if request.user.role != 'ADMIN':
            return Response({'detail': 'Only admins can delete reports.'}, status=status.HTTP_403_FORBIDDEN)
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================
#  COMMENT VIEWS
# =========================

@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_comment(request, report_id):
    try:
        report = Report.objects.get(pk=report_id)
    except Report.DoesNotExist:
        return Response({'detail': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(admin=request.user, report=report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
