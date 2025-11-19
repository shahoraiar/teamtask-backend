from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Task, ActivityLog

@receiver(pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_assigned_to_id = old.assigned_to_id
            instance._old_is_deleted = old.is_deleted
        except sender.DoesNotExist:
            instance._old_assigned_to_id = None
            instance._old_is_deleted = False

@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    user = instance.created_by

    if created:
        ActivityLog.objects.create(task=instance, user=user, action='created', 
                                   note=f"Task '{instance.title}' created")
        return

    old_assigned = getattr(instance, '_old_assigned_to_id', None)
    if instance.assigned_to_id != old_assigned:
        ActivityLog.objects.create(task=instance, user=user,action='assigned',
                                   note=f"Assigned to {instance.assigned_to}")
        return

    old_deleted = getattr(instance, '_old_is_deleted', False)
    if instance.is_deleted and not old_deleted:
        ActivityLog.objects.create(task=instance, user=user, action='deleted',
                                   note=f"Task '{instance.title}' deleted")
        return

    ActivityLog.objects.create(
        task=instance, user=user, action='updated',
        note=f"Task '{instance.title}' updated"
    )