from django.test import TestCase
from django.db.utils import IntegrityError
from authentication.models.user_model import User

class UserModelTest(TestCase):
    """Test suite for the User model."""

    def test_create_user(self):
        """Test that a user can be created successfully."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        
        # Test the string representation
        self.assertEqual(str(user), 'testuser')

    def test_create_superuser(self):
        """Test that a superuser can be created successfully."""
        admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='password123'
        )
        self.assertEqual(admin_user.username, 'adminuser')
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(str(admin_user), 'adminuser')

    def test_email_is_unique(self):
        """Test that two users cannot be created with the same email."""
        User.objects.create_user(
            username='testuser1',
            email='test@example.com',
            password='password123'
        )
        # Use a context manager to assert that an IntegrityError is raised
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser2',
                email='test@example.com', # Same email
                password='password456'
            )


