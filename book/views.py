import logging
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Book, BorrowedBook,  Notification
from .serializers import BookSerializer, BorrowedBookSerializer, NotificationSerializer
from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from .models import Notification


logger = logging.getLogger('library.books')

@api_view(['GET', 'POST'])
def book_list_create(request):
    if request.method == 'GET':
        logger.info(f"User {request.user.username} (ID: {request.user.id}) requested book list")
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        logger.info(f"User {request.user.username} (ID: {request.user.id}) attempting to create new book: {request.data.get('title', 'unknown title')}")
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            book = serializer.save()
            logger.info(f"Book created successfully: '{book.title}' (ID: {book.id}) by {request.user.username}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Book creation failed due to validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def book_detail(request, pk):
    try:
        book = Book.objects.get(pk=pk)
        logger.info(f"Book '{book.title}' (ID: {pk}) accessed by user {request.user.username}")
    except Book.DoesNotExist:
        logger.warning(f"User {request.user.username} attempted to access non-existent book with ID: {pk}")
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BookSerializer(book)
        return Response(serializer.data)
    elif request.method == 'PUT':
        logger.info(f"User {request.user.username} attempting to update book: '{book.title}' (ID: {pk})")
        serializer = BookSerializer(book, data=request.data)
        if serializer.is_valid():
            updated_book = serializer.save()
            logger.info(f"Book updated successfully: '{updated_book.title}' (ID: {pk}) by {request.user.username}")
            return Response(serializer.data)
        logger.warning(f"Book update failed due to validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        book_title = book.title
        logger.info(f"User {request.user.username} attempting to delete book: '{book_title}' (ID: {pk})")
        book.delete()
        logger.info(f"Book '{book_title}' (ID: {pk}) deleted successfully by {request.user.username}")
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def borrow_book(request):
    book_id = request.data.get('book_id')
    user = request.user
    logger.info(f"User {user.username} (ID: {user.id}) attempting to borrow book with ID: {book_id}")

    try:
        book = Book.objects.get(id=book_id)
        if book.available_copies > 0:
            book.available_copies -= 1
            book.save()
            borrowed_book = BorrowedBook.objects.create(user=user, book=book)
            logger.info(f"Book '{book.title}' (ID: {book_id}) successfully borrowed by {user.username}. Due date: {borrowed_book.due_date}")
            serializer = BorrowedBookSerializer(borrowed_book)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            logger.warning(f"User {user.username} attempted to borrow '{book.title}' (ID: {book_id}) but no copies available")
            return Response({"error": "No available copies"}, status=status.HTTP_400_BAD_REQUEST)
    except Book.DoesNotExist:
        logger.warning(f"User {user.username} attempted to borrow non-existent book with ID: {book_id}")
        return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def return_book(request):
    borrowed_book_id = request.data.get('borrowed_book_id')
    user = request.user
    logger.info(f"User {user.username} (ID: {user.id}) attempting to return borrowed book with ID: {borrowed_book_id}")

    try:
        borrowed_book = BorrowedBook.objects.get(id=borrowed_book_id)
        if not borrowed_book.returned:
            borrowed_book.returned = True
            borrowed_book.book.available_copies += 1
            borrowed_book.book.save()
            borrowed_book.save()
            logger.info(f"Book '{borrowed_book.book.title}' (ID: {borrowed_book.book.id}) successfully returned by {user.username}")
            serializer = BorrowedBookSerializer(borrowed_book)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            logger.warning(f"User {user.username} attempted to return already returned book: {borrowed_book.book.title}")
            return Response({"error": "Book already returned"}, status=status.HTTP_400_BAD_REQUEST)
    except BorrowedBook.DoesNotExist:
        logger.warning(f"User {user.username} attempted to return non-existent borrowed book with ID: {borrowed_book_id}")
        return Response({"error": "Borrowed book not found"}, status=status.HTTP_404_NOT_FOUND)
    


@shared_task
def create_due_date_notifications():
    """
    Create notifications for books due soon (3 days before due date) and overdue books.
    """
    logger.info("TASK: Running due date notification check")
    today = timezone.now()
    due_soon_date = today + timedelta(days=3)

    due_soon_books = BorrowedBook.objects.filter(
        due_date__date=due_soon_date.date(),
        returned=False
    )

    overdue_books = BorrowedBook.objects.filter(
        due_date__lt=today,
        returned=False
    )

    notifications_created = 0

    for borrowed_book in due_soon_books:
        if not Notification.objects.filter(
            borrowed_book=borrowed_book,
            notification_type='due_soon',
            created_at__gt=today - timedelta(days=1)
        ).exists():
            message = f"Your book '{borrowed_book.book.title}' is due in 3 days on {borrowed_book.due_date.strftime('%Y-%m-%d')}."
            Notification.objects.create(
                user=borrowed_book.user,
                borrowed_book=borrowed_book,
                notification_type='due_soon',
                message=message
            )
            notifications_created += 1

    for borrowed_book in overdue_books:
        if not Notification.objects.filter(
            borrowed_book=borrowed_book,
            notification_type='overdue',
            created_at__gt=today - timedelta(days=1)
        ).exists():
            days_overdue = (today - borrowed_book.due_date).days
            message = f"Your book '{borrowed_book.book.title}' is {days_overdue} days overdue."
            Notification.objects.create(
                user=borrowed_book.user,
                borrowed_book=borrowed_book,
                notification_type='overdue',
                message=message
            )
            notifications_created += 1

    logger.info(f"TASK: Created {notifications_created} new due date notifications")
    return notifications_created



@api_view(['GET'])
def list_notifications(request):
    """
    API to list all notifications for the authenticated user.
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def mark_notification_as_read(request, notification_id):
    """
    API to mark a notification as read.
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.status = "sent"
    notification.sent_at = timezone.now()
    notification.save()

    return Response({"message": "Notification marked as read"}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
def delete_notification(request, notification_id):
    """
    API to delete a specific notification.
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()

    return Response({"message": "Notification deleted successfully"}, status=status.HTTP_204_NO_CONTENT)