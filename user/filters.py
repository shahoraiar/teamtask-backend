import django_filters
from .models import Task

class TaskFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    assigned_to = django_filters.NumberFilter(field_name='assigned_to__id')
    due_date = django_filters.DateFilter(field_name='due_date')

    class Meta:
        model = Task
        fields = ['status', 'assigned_to', 'due_date']