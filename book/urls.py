from django.urls import path
from .views import book_list_create, book_detail, borrow_book, return_book
from .views import list_notifications, mark_notification_as_read, delete_notification

urlpatterns = [
    path('books/', book_list_create, name='book-list-create'),
    path('books/<int:pk>/', book_detail, name='book-detail'),
    path('borrow/', borrow_book, name='borrow-book'),
    path('return/', return_book, name='return-book'),
    path('notifications/', list_notifications, name='list_notifications'),
    path('notifications/read/<int:notification_id>/', mark_notification_as_read, name='mark_notification_as_read'),
    path('notifications/delete/<int:notification_id>/', delete_notification, name='delete_notification'),
]
