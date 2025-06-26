from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Asset, Notification, Violation
from .serializers import (
    AssetSerializer, NotificationSerializer, 
    ViolationSerializer, AssetServiceUpdateSerializer
)


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    def get_queryset(self):
        queryset = Asset.objects.all()
        
        # Filter by service status
        is_serviced = self.request.query_params.get('is_serviced')
        if is_serviced is not None:
            queryset = queryset.filter(is_serviced=is_serviced.lower() == 'true')
        
        # Filter by expiration status
        expired = self.request.query_params.get('expired')
        if expired is not None:
            now = timezone.now()
            if expired.lower() == 'true':
                queryset = queryset.filter(expiration_time__lt=now)
            else:
                queryset = queryset.filter(expiration_time__gte=now)
        
        # Filter by service due status
        service_due = self.request.query_params.get('service_due')
        if service_due is not None:
            now = timezone.now()
            if service_due.lower() == 'true':
                queryset = queryset.filter(
                    service_time__lt=now, 
                    is_serviced=False
                )
        
        return queryset

    @extend_schema(
        methods=['patch'],
        request=AssetServiceUpdateSerializer,
        responses={200: AssetSerializer}
    )
    @action(detail=True, methods=['patch'])
    def update_service_status(self, request, pk=None):
        """Update the service status of an asset"""
        asset = self.get_object()
        serializer = AssetServiceUpdateSerializer(
            asset, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(AssetSerializer(asset).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard statistics"""
        now = timezone.now()
        total_assets = Asset.objects.count()
        expired_assets = Asset.objects.filter(expiration_time__lt=now).count()
        service_due = Asset.objects.filter(
            service_time__lt=now, 
            is_serviced=False
        ).count()
        serviced_assets = Asset.objects.filter(is_serviced=True).count()
        
        return Response({
            'total_assets': total_assets,
            'expired_assets': expired_assets,
            'service_due': service_due,
            'serviced_assets': serviced_assets,
        })


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.all()
        
        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by asset
        asset_id = self.request.query_params.get('asset')
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        
        return queryset


class ViolationViewSet(viewsets.ModelViewSet):
    queryset = Violation.objects.all()
    serializer_class = ViolationSerializer

    def get_queryset(self):
        queryset = Violation.objects.all()
        
        # Filter by resolved status
        resolved = self.request.query_params.get('resolved')
        if resolved is not None:
            queryset = queryset.filter(resolved=resolved.lower() == 'true')
        
        # Filter by violation type
        violation_type = self.request.query_params.get('type')
        if violation_type:
            queryset = queryset.filter(violation_type=violation_type)
        
        # Filter by asset
        asset_id = self.request.query_params.get('asset')
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        
        return queryset

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark a violation as resolved"""
        violation = self.get_object()
        violation.resolve()
        return Response({'status': 'violation resolved'})


@extend_schema(
    methods=['post'],
    responses={200: dict},
    description="Run periodic checks for notifications and violations"
)
@api_view(['POST'])
def run_checks(request):
    """
    Manual endpoint to run periodic checks for notifications and violations.
    This simulates the background task functionality.
    """
    from .tasks import check_notifications_and_violations
    
    result = check_notifications_and_violations()
    return Response(result)

# Create your views here.
