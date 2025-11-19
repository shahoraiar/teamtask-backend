from rest_framework import permissions
from .models import TeamMembership, Task

class IsTeamMember(permissions.BasePermission):
    def has_permission(self, request, view):
        team = None
        team_id = view.kwargs.get('team_pk') or request.data.get('team') or request.query_params.get('team')
        if not team_id:
            return False
        return TeamMembership.objects.filter(team_id=team_id, user=request.user).exists()

    def has_object_permission(self, request, view, obj):
        team = getattr(obj, 'team', None)
        if team:
            return TeamMembership.objects.filter(team=team, user=request.user).exists()
        return False

class IsTeamAdmin(permissions.BasePermission):
    def _is_admin(self, user, team):
        return TeamMembership.objects.filter(team=team, user=user, role='admin').exists()

    def has_permission(self, request, view):
        team_id = view.kwargs.get('team_pk') or request.data.get('team') or request.query_params.get('team')
        if not team_id:
            return False
        from .models import Team
        try:
            team = Team.objects.get(pk=team_id)
        except Team.DoesNotExist:
            return False
        return self._is_admin(request.user, team)

    def has_object_permission(self, request, view, obj):
        team = getattr(obj, 'team', None)
        if team:
            return self._is_admin(request.user, team)
        return False

class IsTaskAssignee(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Task):
            return False
        return obj.assigned_to_id == request.user.id
