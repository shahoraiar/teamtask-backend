from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Task, ActivityLog

@receiver(post_save, sender=Task)
def task_post_save(sender, instance: Task, created, **kwargs):
    user = instance.created_by
    if created:
        ActivityLog.objects.create(task=instance, user=user, action='created', note=f"Task {instance.title} created")
    else:
        try:
            old = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            old = None

        ActivityLog.objects.create(task=instance, user=instance.created_by, action='updated', note=f"Task updated")

from django.db.models.signals import pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_assigned_to_id = old.assigned_to_id
        except sender.DoesNotExist:
            instance._old_assigned_to_id = None

@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    user = instance.created_by
    if created:
        ActivityLog.objects.create(task=instance, user=user, action='created', note=f"Task created")
    else:
        old_assigned = getattr(instance, '_old_assigned_to_id', None)
        if instance.assigned_to_id != old_assigned:
            ActivityLog.objects.create(task=instance, user=user, action='assigned', note=f"Assigned to {instance.assigned_to}")
        else:
            ActivityLog.objects.create(task=instance, user=user, action='updated', note=f"Task updated")

