from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DjangoAdminAccessTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            email='admin@example.com',
            password='valid-test-password-2026',
            first_name='Admin',
            kind='admin',
            status='active',
        )

    def test_active_admin_role_can_access_admin_and_application_models(self):
        self.assertTrue(self.admin.is_staff)
        self.assertTrue(self.admin.has_perm('companies.view_company'))
        self.assertTrue(self.client.login(
            username=self.admin.email,
            password='valid-test-password-2026',
        ))
        response = self.client.get(reverse('admin:companies_company_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_users_with_hashed_passwords(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin:accounts_user_add'), {
            'email': 'new-client@example.com',
            'first_name': 'New',
            'last_name': 'Client',
            'kind': 'client',
            'status': 'active',
            'is_active': 'on',
            'password1': 'Deltablock-New-2026!',
            'password2': 'Deltablock-New-2026!',
            '_save': 'Save',
        })

        self.assertEqual(response.status_code, 302)
        created = get_user_model().objects.get(email='new-client@example.com')
        self.assertTrue(created.check_password('Deltablock-New-2026!'))

    def test_client_role_cannot_access_django_admin(self):
        user = get_user_model().objects.create_user(
            email='client@example.com',
            password='valid-test-password-2026',
            first_name='Client',
            kind='client',
            status='active',
        )

        self.assertFalse(user.is_staff)
        self.assertTrue(self.client.login(
            username=user.email,
            password='valid-test-password-2026',
        ))
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 302)

    def test_superuser_can_open_django_admin(self):
        user = get_user_model().objects.create_superuser(
            email='superuser@example.com',
            password='valid-test-password-2026',
            first_name='Superuser',
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(self.client.login(
            username=user.email.upper(),
            password='valid-test-password-2026',
        ))
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
