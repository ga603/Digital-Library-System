from django.contrib import admin
from .models import User, Category, Book, BorrowRecord

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'quantity_available', 'shelf_no')
    search_fields = ('title', 'isbn')

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'issue_date', 'due_date', 'status')
    list_filter = ('status', 'issue_date')

admin.site.register(User)
admin.site.register(Category)