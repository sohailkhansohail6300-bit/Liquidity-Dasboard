from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('An email address is required.')
        user = self.model(email=email.strip(), **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('kind', User.Kind.ADMIN)
        extra.setdefault('status', User.Status.ACTIVE)
        extra.setdefault('is_active', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('via', 'Created with createsuperuser')
        if extra.get('kind') != User.Kind.ADMIN:
            raise ValueError('A superuser must have the admin role.')
        if extra.get('status') != User.Status.ACTIVE:
            raise ValueError('A superuser must have active status.')
        if not extra.get('is_active'):
            raise ValueError('A superuser must be active.')
        if not extra.get('is_superuser'):
            raise ValueError('A superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Everyone with an account or a pending invitation (the prototype's ``people`` list).

    Company access and Team-management rights are *not* stored here: they live in
    ``companies.CompanyAccess`` (one row per person and company, with ``can_manage``).
    """

    class Kind(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CLIENT = 'client', 'Client'
        COLLEAGUE = 'colleague', 'Colleague'
        GUEST = 'guest', 'Guest'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PENDING = 'pending', 'Pending'

    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60, blank=True, default='')
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.CLIENT)
    is_owner = models.BooleanField(default=False, help_text='Account owner of a client tenant.')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    via = models.CharField(max_length=60, blank=True, default='')
    invited_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='invitees')
    invited_by_name = models.CharField(max_length=120, blank=True, default='')
    tenant_owner = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name='tenant_members',
                                     help_text='Account owner this person belongs to. Empty for owners themselves.')
    setup_token = models.CharField(max_length=96, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False, help_text='Seeded demonstration account.')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(Lower('email'), name='uniq_user_email_ci'),
        ]
        indexes = [
            models.Index(fields=['kind', 'status'], name='user_kind_status_idx'),
        ]

    def __str__(self):
        return self.email

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def is_admin(self):
        return self.kind == self.Kind.ADMIN

    @property
    def is_guest(self):
        return self.kind == self.Kind.GUEST

    @property
    def can_use_portal(self):
        return self.is_active and self.status == self.Status.ACTIVE

    @property
    def is_staff(self):
        return (
            self.is_active
            and self.status == self.Status.ACTIVE
            and (self.is_admin or self.is_superuser)
        )

    def has_perm(self, perm, obj=None):
        if self.is_admin and self.is_staff:
            return True
        if not self.is_staff:
            return False
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_admin and self.is_staff:
            return True
        if not self.is_staff:
            return False
        return super().has_module_perms(app_label)

    def save(self, *args, **kwargs):
        self.email = (self.email or '').strip()
        super().save(*args, **kwargs)
