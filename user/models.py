from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        LIBRARIAN = "librarian", "Librarian"
        MEMBER = "member", "Member"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER
    )

    def __str__(self):
        return f"{self.username} - {self.role}"