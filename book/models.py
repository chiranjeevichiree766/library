from django.db import models
from datetime import timedelta
from user.models import CustomUser


class Book(models.Model):
    title = models.CharField(max_length=255, blank=False)
    author = models.CharField(max_length=255, blank=False)
    isbn = models.CharField(max_length=13, unique=True, blank=False)
    published_date = models.DateField(blank=True, null=True)
    pages = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()

    def __str__(self):
        return self.title



class BorrowedBook(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True)
    returned = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.borrowed_at + timedelta(days=15)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book.title} borrowed by {self.user.username}"



class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue'),
        ('returned', 'Returned'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    borrowed_book = models.ForeignKey(BorrowedBook, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.user.username} - {self.borrowed_book.book.title}"