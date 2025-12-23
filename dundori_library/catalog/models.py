from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date

# 1. USER MODEL (Only for Librarians/Admins now)
class User(AbstractUser):
    # We remove student-specific fields since they won't log in
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('LIBRARIAN', 'Librarian'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='LIBRARIAN')

    def __str__(self):
        return self.username

# 2. STUDENT MODEL (New! Just a list of names)
class Student(models.Model):
    CLASS_CHOICES = (
        ('GRADE 10', 'Grade 10'), ('GRADE 11', 'Grade 11'), ('GRADE 12', 'Grade 12'),
        ('FORM 3', 'Form 3'), ('FORM 4', 'Form 4'),
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    admission_number = models.CharField(max_length=20, unique=True)
    student_class = models.CharField(max_length=20, choices=CLASS_CHOICES)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"

# 3. CATEGORY & BOOK (Same as before)
class Category(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name
    class Meta: verbose_name_plural = "Categories"

class Book(models.Model):
    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    author = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    quantity_total = models.PositiveIntegerField(default=1)
    quantity_available = models.PositiveIntegerField(default=1)
    shelf_no = models.CharField(max_length=20, blank=True)
    
    def __str__(self): return f"{self.title} ({self.quantity_available} avail)"

# 4. BORROW RECORD (Updated to link to Student model)
class BorrowRecord(models.Model):
    # CHANGED: Links to Student model, not User model
    student = models.ForeignKey(Student, on_delete=models.CASCADE) 
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, default='ISSUED')

    def calculate_fine(self):
        if self.return_date and self.return_date > self.due_date:
            return (self.return_date - self.due_date).days * 5
        elif not self.return_date and date.today() > self.due_date:
            return (date.today() - self.due_date).days * 5
        return 0