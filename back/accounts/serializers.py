from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Employee

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = ('id', 'role')


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'date_joined',
            'registration_dttm'
        )
        read_only_fields = (
            'id',
            'role',
            'is_active',
            'date_joined',
            'registration_dttm'
        )


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'password',
            'password2',
            'email',
            'first_name',
            'last_name',
            'role'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Пароли не совпадают"}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    manager_name = serializers.SerializerMethodField()
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = (
            'id',
            'user',
            'hire_dt',
            'position',
            'manager',
            'manager_name',
            'profile_photo',
            'profile_photo_url'
        )
        read_only_fields = ('id', 'user', 'profile_photo_url')

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.user.get_full_name()
        return None
        
    def get_profile_photo_url(self, obj):
        if obj.profile_photo:
            return obj.profile_photo.url
        return None


class EmployeeDetailSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)
    subordinates = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    is_manager = serializers.SerializerMethodField()
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = (
            'id',
            'user',
            'hire_dt',
            'position',
            'manager',
            'manager_name',
            'subordinates',
            'is_manager',
            'profile_photo_url'
        )
        read_only_fields = ('id', 'user', 'is_manager', 'profile_photo_url')

    def get_subordinates(self, obj):
        return EmployeeSerializer(obj.subordinates.all(), many=True).data

    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.user.get_full_name()
        return None

    def get_is_manager(self, obj):
        return obj.subordinates.exists()
        
    def get_profile_photo_url(self, obj):
        if obj.profile_photo:
            return obj.profile_photo.url
        return None


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True)

    class Meta:
        model = Employee
        fields = ('user_id', 'hire_dt', 'position', 'manager', 'profile_photo')

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким ID не существует")

        if Employee.objects.filter(user_id=value).exists():
            raise serializers.ValidationError(
                "Профиль сотрудника для этого пользователя уже существует")

        return value

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        employee = Employee.objects.create(user=user, **validated_data)
        return employee


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.get_full_name()

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        data['user_id'] = user.id
        data['username'] = user.username
        data['email'] = user.email
        data['role'] = user.role
        data['full_name'] = user.get_full_name()

        try:
            employee = user.employee_profile
            data['employee_id'] = employee.id
            data['position'] = employee.position
            data['has_employee_profile'] = True
            data['is_manager'] = employee.subordinates.exists()
            if employee.profile_photo:
                data['profile_photo_url'] = employee.profile_photo.url
        except Employee.DoesNotExist:
            data['has_employee_profile'] = False
            data['is_manager'] = False

        return data
