from rest_framework import serializers
from .models import Book, BorrowedBook
from .models import Notification

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class BorrowedBookSerializer(serializers.ModelSerializer):
    book = BookSerializer()
    user = serializers.StringRelatedField()

    class Meta:
        model = BorrowedBook
        fields = '__all__'




class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
