from django.utils import timezone
from datetime import timedelta
from .models import Asset, Notification, Violation


def check_notifications_and_violations():
    
    now = timezone.now()
    reminder_time = timedelta(minutes=15)
    
    notifications_created = 0
    violations_created = 0
    
    
    for asset in Asset.objects.all():
        
        if asset.service_time and not asset.is_serviced:
            time_to_service = asset.service_time - now
            if timedelta(0) <= time_to_service <= reminder_time:
                # Check if notification already exists
                existing_notification = Notification.objects.filter(
                    asset=asset,
                    notification_type='service_reminder'
                ).exists()
                
                if not existing_notification:
                    Notification.objects.create(
                        asset=asset,
                        notification_type='service_reminder',
                        message=f"Service reminder: {asset.name} is due for service in {time_to_service}",
                        is_sent=True
                    )
                    notifications_created += 1
        
        # Check for expiration reminders (15 minutes before expiration)
        if asset.expiration_time:
            time_to_expiration = asset.expiration_time - now
            if timedelta(0) <= time_to_expiration <= reminder_time:
                # Check if notification already exists
                existing_notification = Notification.objects.filter(
                    asset=asset,
                    notification_type='expiration_reminder'
                ).exists()
                
                if not existing_notification:
                    Notification.objects.create(
                        asset=asset,
                        notification_type='expiration_reminder',
                        message=f"Expiration reminder: {asset.name} will expire in {time_to_expiration}",
                        is_sent=True
                    )
                    notifications_created += 1
        
        # Check for violations
        # Service overdue violation
        if asset.service_time and asset.service_time < now and not asset.is_serviced:
            existing_violation = Violation.objects.filter(
                asset=asset,
                violation_type='service_overdue',
                resolved=False
            ).exists()
            
            if not existing_violation:
                Violation.objects.create(
                    asset=asset,
                    violation_type='service_overdue',
                    description=f"Asset {asset.name} has overdue service. Service was due at {asset.service_time}"
                )
                violations_created += 1
        
        # Expired and not serviced violation
        if asset.expiration_time and asset.expiration_time < now and not asset.is_serviced:
            existing_violation = Violation.objects.filter(
                asset=asset,
                violation_type='expired_not_serviced',
                resolved=False
            ).exists()
            
            if not existing_violation:
                Violation.objects.create(
                    asset=asset,
                    violation_type='expired_not_serviced',
                    description=f"Asset {asset.name} has expired and was not serviced. Expired at {asset.expiration_time}"
                )
                violations_created += 1
    
    return {
        'status': 'completed',
        'notifications_created': notifications_created,
        'violations_created': violations_created,
        'checked_at': now.isoformat()
    }