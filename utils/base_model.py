import uuid
from django.db import models
from django.apps import apps
from django.db.models.fields.related import OneToOneRel

from django_currentuser.middleware import get_current_user
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

from django.contrib.auth.models import User
from celery import shared_task


@shared_task
def soft_delete_related_objects(app_label, model_name, instance_pk, using=None):
    """
    Soft delete related objects for a given model instance
    """
    # Get the model class using app registry
    model_class = apps.get_model(app_label, model_name)

    # Get the instance using all_objects to ensure we can get even if it's already soft deleted
    try:
        instance = model_class.all_objects.get(pk=instance_pk)
    except model_class.DoesNotExist:
        return

    # Get all related fields that are reverse relationships
    all_related = [
        f
        for f in instance._meta.get_fields()
        if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
    ]

    # Handle each related field
    for relation in all_related:
        related_name = relation.get_accessor_name()

        # Skip if the relation doesn't exist
        if not hasattr(instance, related_name):
            continue

        # Get the on_delete behavior name
        on_delete_name = (
            relation.on_delete.__name__
            if hasattr(relation.on_delete, "__name__")
            else ""
        )

        if on_delete_name == "DO_NOTHING":
            continue

        elif on_delete_name == "SET_NULL":
            # Handle SET_NULL relationships
            if isinstance(relation, OneToOneRel):
                # For OneToOne relationships
                related_obj = getattr(instance, related_name, None)
                if related_obj and isinstance(related_obj, models.Model):
                    setattr(related_obj, relation.remote_field.name, None)
                    related_obj.save(update_fields=[relation.remote_field.name])
            else:
                # For other relationships
                related_queryset = getattr(instance, related_name).all()
                related_queryset.update(**{relation.remote_field.name: None})

        else:
            # Handle CASCADE and other delete behaviors
            try:
                if relation.one_to_one:
                    # Handle OneToOne relationships
                    related_obj = getattr(instance, related_name, None)
                    if related_obj:
                        if hasattr(related_obj, "deleted_at"):
                            if not related_obj.deleted_at:
                                related_obj.deleted_at = timezone.now()
                                related_obj.save()
                                # Recursively handle related objects
                                soft_delete_related_objects(
                                    related_obj._meta.app_label,
                                    related_obj._meta.model_name,
                                    related_obj.pk,
                                    using,
                                )
                else:
                    # Handle other relationships
                    related_queryset = getattr(instance, related_name)(
                        manager="objects"
                    ).all()

                    for related_obj in related_queryset:
                        if hasattr(related_obj, "deleted_at"):
                            if not related_obj.deleted_at:
                                related_obj.deleted_at = timezone.now()
                                related_obj.save()
                                # Recursively handle related objects
                                soft_delete_related_objects(
                                    related_obj._meta.app_label,
                                    related_obj._meta.model_name,
                                    related_obj.pk,
                                    using,
                                )
            except Exception as e:
                # Log the error or handle as needed
                print(f"Error handling relation {related_name}: {str(e)}")
                continue

    # Finally, soft delete the instance itself if it hasn't been deleted yet
    if hasattr(instance, "deleted_at") and not instance.deleted_at:
        instance.deleted_at = timezone.now()
        instance.save()


# @shared_task
def restore_related_objects(app_label, model_name, instance_pk, using=None):
    pass


class TimeAuditModel(models.Model):
    """To path when the record was created and last modified"""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Modified At")

    class Meta:
        abstract = True


class UserAuditModel(models.Model):
    """To path when the record was created and last modified"""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created_by",
        verbose_name="Created By",
        null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated_by",
        verbose_name="Last Modified By",
        null=True,
    )

    class Meta:
        abstract = True


class SoftDeletionQuerySet(models.QuerySet):
    def delete(self, soft=True):
        if soft:
            return self.update(deleted_at=timezone.now())
        else:
            return super().delete()


class SoftDeletionManager(models.Manager):
    def get_queryset(self):
        return SoftDeletionQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=True
        )


class SoftDeleteModel(models.Model):
    """To soft delete records"""

    deleted_at = models.DateTimeField(verbose_name="Deleted At", null=True, blank=True)

    objects = SoftDeletionManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, soft=True, *args, **kwargs):
        if soft:
            # Soft delete the current instance
            self.deleted_at = timezone.now()
            self.save(using=using)

            soft_delete_related_objects.delay(
                self._meta.app_label, self._meta.model_name, self.pk, using=using
            )

        else:
            # Perform hard delete if soft deletion is not enabled
            return super().delete(using=using, *args, **kwargs)


class AuditModel(TimeAuditModel, UserAuditModel, SoftDeleteModel):
    """To path when the record was created and last modified"""

    class Meta:
        abstract = True


class BaseModel(AuditModel):
    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, editable=False, db_index=True, primary_key=True
    # )

    class Meta:
        abstract = True

    def clean(self):
        # Validate uniqueness manually if unique_fields are defined
        if self.unique_fields:
            query = self.__class__.all_objects.filter(deleted_at__isnull=True)
            for field in self.unique_fields:
                value = getattr(self, field)
                query = query.filter(**{field: value})
            if self.pk:
                query = query.exclude(pk=self.pk)
            if query.exists():
                raise ValidationError({field: f"{field} must be unique." for field in self.unique_fields})


    def save(self, *args, created_by_id=None, disable_auto_set_user=False, **kwargs):
        self.clean() 
        if not disable_auto_set_user:
            # Check if created_by_id is provided
            if created_by_id:
                self.created_by_id = created_by_id
            else:
                user = get_current_user()

                if user is None or user.is_anonymous:
                    self.created_by = None
                    self.updated_by = None
                else:
                    # Check if the model is being created or updated
                    if self._state.adding:
                        # If creating, set created_by and leave updated_by as None
                        self.created_by = user
                        self.updated_by = None
                    else:
                        # If updating, set updated_by only
                        self.updated_by = user

        super(BaseModel, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.id)
