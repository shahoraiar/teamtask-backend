from django.shortcuts import render
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import *
from .serializers import *
from .permissions import *
from .filters import TaskFilter
from rest_framework import filters

from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    queryset = User.objects.all()

class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     user = self.request.user
    #     return Company.objects.filter(
    #         Q(owner=user) |
    #         Q(teams__memberships__user=user)
    #     ).distinct()
    def get_queryset(self):
        # FIX for Swagger Anonymous User
        if getattr(self, 'swagger_fake_view', False):
            return Company.objects.none()

        user = self.request.user
        return Company.objects.filter(
            Q(owner=user) |
            Q(teams__memberships__user=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     company_id = self.request.query_params.get('company')
    #     qs = Team.objects.all()
    #     if company_id:
    #         qs = qs.filter(company_id=company_id)
    #     qs = qs.filter(Q(company__owner=self.request.user) | Q(memberships__user=self.request.user)).distinct()
    #     return qs
    def get_queryset(self):
        # FIX for Swagger Anonymous User
        if getattr(self, 'swagger_fake_view', False):
            return Team.objects.none()

        company_id = self.request.query_params.get('company')
        qs = Team.objects.all()

        if company_id:
            qs = qs.filter(company_id=company_id)

        return qs.filter(
            Q(company__owner=self.request.user) |
            Q(memberships__user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        team = serializer.save()
        TeamMembership.objects.create(user=self.request.user, team=team, role='admin')

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        team = self.get_object()
        members = TeamMembership.objects.filter(team=team)
        serializer = TeamMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        team = self.get_object()
        if not TeamMembership.objects.filter(team=team, user=request.user, role='admin').exists():
            return Response({'detail': 'Only admins can add members'}, status=403)
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')
        user = get_object_or_404(User, pk=user_id)
        membership, created = TeamMembership.objects.get_or_create(team=team, user=user, defaults={'role': role})
        if not created:
            membership.role = role
            membership.save()
        return Response(TeamMemberSerializer(membership).data)

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        team = self.get_object()
        if not TeamMembership.objects.filter(team=team, user=request.user, role='admin').exists():
            return Response({'detail': 'Only admins can remove members'}, status=403)
        user_id = request.data.get('user_id')
        membership = get_object_or_404(TeamMembership, team=team, user_id=user_id)
        if membership.user == team.company.owner:
            return Response({'detail': 'Cannot remove company owner'}, status=400)
        membership.delete()
        return Response({'detail': 'removed'})

    @action(detail=True, methods=['post'], url_path='change-role')
    def change_role(self, request, pk=None):
        team = self.get_object()
        if not TeamMembership.objects.filter(team=team, user=request.user, role='admin').exists():
            return Response({'detail': 'Only admins can change roles'}, status=403)
        user_id = request.data.get('user_id')
        role = request.data.get('role')
        membership = get_object_or_404(TeamMembership, team=team, user_id=user_id)
        membership.role = role
        membership.save()
        return Response(TeamMemberSerializer(membership).data)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TaskFilter
    search_fields = ['title', 'description'] 
    ordering_fields = ['due_date', 'created_at']
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()

        qs = Task.objects.filter(is_deleted=False)
        return qs.filter(team__memberships__user=self.request.user).distinct()

    def perform_create(self, serializer):
        team = serializer.validated_data['team']
        if not TeamMembership.objects.filter(team=team, user=self.request.user, role='admin').exists():
            return Response({'detail': 'Only team admins can create tasks'}, status=403)
        serializer.save(created_by=self.request.user)

    def get_serializer_class(self):
        if self.action in ['partial_update', 'update']:
            return TaskSerializer
        return TaskSerializer

    def perform_destroy(self, instance):
        if not TeamMembership.objects.filter(team=instance.team, user=self.request.user, role='admin').exists():
            raise PermissionError("Only admins can delete")
        instance.soft_delete()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if TeamMembership.objects.filter(team=instance.team, user=request.user, role='admin').exists():
            return super().update(request, *args, **kwargs)
        if TeamMembership.objects.filter(team=instance.team, user=request.user).exists():
            serializer = TaskUpdateMemberSerializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(TaskSerializer(instance).data)
        return Response({'detail': 'Not allowed'}, status=403)

    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None):
        instance = self.get_object()
        if not TeamMembership.objects.filter(team=instance.team, user=request.user, role='admin').exists():
            return Response({'detail': 'Only admins can assign tasks'}, status=403)
        user_id = request.data.get('user_id')
        user = get_object_or_404(User, pk=user_id)
        if not TeamMembership.objects.filter(team=instance.team, user=user).exists():
            return Response({'detail': 'User not a member of the team'}, status=400)
        instance.assigned_to = user
        instance.save()
        return Response(TaskSerializer(instance).data)

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()
        
        user = self.request.user
        return ActivityLog.objects.filter(
            task__team__memberships__user=user
        ).order_by('-timestamp') 

        

