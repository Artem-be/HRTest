from rest_framework import serializers
from .models import UserControl

class UserControlSerializers(serializers.ModelSerializer):
    class Meta:
        model = UserControl
        fields = ['tg_id', 'name', 'number_phone', 'service']