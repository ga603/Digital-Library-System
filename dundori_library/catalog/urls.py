from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='catalog/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('books/', views.book_list, name='book_list'),
    path('issue/', views.issue_book, name='issue_book'),
    path('return/', views.active_loans, name='active_loans'),              
    path('return/<int:pk>/', views.return_book_action, name='return_book_action'),
    path('add-student/', views.add_student, name='add_student'),
    path('upload/', views.upload_books, name='upload_books'),
    path('student/<int:pk>/', views.student_history, name='student_history'),
    path('students/', views.student_list, name='student_list'),
    path('', views.landing_page, name='landing_page'),
    path('dashboard/', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='catalog/login.html'), name='login'),
]