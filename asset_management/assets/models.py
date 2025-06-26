from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator

class Asset(models.Model):
    name = models.CharField(
        max_length=200, 
        validators=[MinLengthValidator(2)],
        help_text="Asset name (minimum 2 characters)"
    )
    description = models.TextField(blank=True, help_text="Asset description")
    service_time = models.DateTimeField(
        help_text="When maintenance/service is due"
    )
    expiration_time = models.DateTimeField(
        help_text="When the asset is no longer valid"
    )
    is_serviced = models.BooleanField(
        default=False, 
        help_text="Whether the asset has been serviced"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service_time']),
            models.Index(fields=['expiration_time']),
            models.Index(fields=['is_serviced']),
        ]

    def __str__(self):
        return f"{self.name} - Service: {self.service_time}, Expires: {self.expiration_time}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.service_time and self.expiration_time:
            if self.service_time >= self.expiration_time:
                raise ValidationError("Service time must be before expiration time")
            


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expiration_time

    @property
    def is_service_due(self):
        return timezone.now() > self.service_time and not self.is_serviced


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('service_reminder', 'Service Reminder'),
        ('expiration_reminder', 'Expiration Reminder'),
    ]

    asset = models.ForeignKey(
        Asset, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset', 'notification_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.asset.name}"


class Violation(models.Model):
    VIOLATION_TYPES = [
        ('expired_not_serviced', 'Expired and Not Serviced'),
        ('service_overdue', 'Service Overdue'),
    ]

    asset = models.ForeignKey(
        Asset, 
        on_delete=models.CASCADE, 
        related_name='violations'
    )
    violation_type = models.CharField(
        max_length=20, 
        choices=VIOLATION_TYPES
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset', 'violation_type']),
            models.Index(fields=['resolved']),
        ]

    def __str__(self):
        return f"{self.get_violation_type_display()} for {self.asset.name}"

    def resolve(self):
        self.resolved = True
        self.resolved_at = timezone.now()
        self.save()

