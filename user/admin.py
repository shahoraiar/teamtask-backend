from django.contrib import admin
from .models import User, Company, Team, TeamMembership, Task, ActivityLog
# Register your models here.

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'user', 'action', 'timestamp', 'note')
    list_filter = ('action', 'timestamp')
    search_fields = ('task__title', 'user__username', 'note')

admin.site.register(User)
admin.site.register(Company)
admin.site.register(Team)
admin.site.register(TeamMembership)
admin.site.register(Task)