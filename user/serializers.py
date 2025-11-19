from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Company, Team, TeamMembership, Task, ActivityLog

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class CompanySerializer(serializers.ModelSerializer):
    owner = UserProfileSerializer(read_only=True)

    class Meta:
        model = Company
        fields = ('id', 'name', 'owner', 'created_at')

class TeamSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    class Meta:
        model = Team
        fields = ('id', 'company', 'name', 'description', 'created_at')

class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(write_only=True, source='user', queryset=User.objects.all())
    role = serializers.ChoiceField(choices=TeamMembership.ROLE_CHOICES)

    class Meta:
        model = TeamMembership
        fields = ('id', 'team', 'user', 'user_id', 'role', 'joined_at')
        read_only_fields = ('joined_at', 'team', 'user')

class TaskSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(write_only=True, source='assigned_to', queryset=User.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Task
        fields = ('id', 'team', 'title', 'description', 'created_by', 'assigned_to', 'assigned_to_id', 'status', 'due_date', 'created_at', 'updated_at')
        read_only_fields = ('created_by', 'created_at', 'updated_at')

class TaskUpdateMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('status', 'description')

class ActivityLogSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    task = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = ActivityLog
        fields = ('id', 'task', 'user', 'action', 'timestamp', 'note')
