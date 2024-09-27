from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    phone_number = models.CharField(max_length=12, null=True)
    profile_image = models.ImageField(upload_to='uploads/', null=True)
    country = models.CharField(max_length=250, null=True)
    status = models.IntegerField(default=0, verbose_name='status', null=True)
    role = models.CharField(max_length=250, null=True)

    # Adding related_name to prevent reverse accessor clashes
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_groups',  # Change the related_name to avoid conflict
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions',  # Change the related_name to avoid conflict
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

from django.db import models

class AuthCode(models.Model):
    code = models.CharField(max_length=100, unique=True)  # Adjust max_length as needed
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the code was created
    # is_used = models.BooleanField(default=False)  # To track if the code has been used

    def __str__(self):
        return f"AuthCode(code={self.code}, user={self.user.username}, is_used={self.is_used})"



