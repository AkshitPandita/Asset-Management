from rest_framework import serializers
from django.utils import timezone
from .models import Asset, Notification, Violation





class AssetSerializer(serializers.ModelSerializer):
    is_expired = serializers.ReadOnlyField()
    is_service_due = serializers.ReadOnlyField()

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'description', 'service_time', 
            'expiration_time', 'is_serviced', 'is_expired', 
            'is_service_due', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        if data.get('service_time') and data.get('expiration_time'):
            if data['service_time'] >= data['expiration_time']:
                raise serializers.ValidationError(
                    "Service time must be before expiration time"
                )
        
    
        if not self.instance:  
            now = timezone.now()
            if data.get('service_time') and data['service_time'] <= now:
                raise serializers.ValidationError(
                    "Service time must be in the future"
                )
            if data.get('expiration_time') and data['expiration_time'] <= now:
                raise serializers.ValidationError(
                    "Expiration time must be in the future"
                )
        
        return data


class NotificationSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'asset', 'asset_name', 'notification_type', 
            'message', 'created_at', 'is_sent'
        ]
        read_only_fields = ['created_at']


class ViolationSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = Violation
        fields = [
            'id', 'asset', 'asset_name', 'violation_type', 
            'description', 'created_at', 'resolved', 'resolved_at'
        ]
        read_only_fields = ['created_at', 'resolved_at']


class AssetServiceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['is_serviced']

    def update(self, instance, validated_data):
        instance.is_serviced = validated_data.get('is_serviced', instance.is_serviced)
        instance.save()
        return instance