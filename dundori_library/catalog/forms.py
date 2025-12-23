from django import forms
from .models import BorrowRecord, Book, Student

# 1. ISSUE BOOK FORM (Updated)
class IssueBookForm(forms.ModelForm):
    # Select from the Student list, not User list
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(quantity_available__gt=0),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = BorrowRecord
        fields = ['student', 'book', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

# 2. STUDENT REGISTRATION FORM (New & Simple)
class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'admission_number', 'student_class']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'admission_number': forms.TextInput(attrs={'class': 'form-control'}),
            'student_class': forms.Select(attrs={'class': 'form-select'}),
        }
# ... existing imports ...

# 1. NEW FORM FOR CSV UPLOAD
class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV/Excel File")

# 2. UPDATE ISSUE BOOK FORM (To allow manual typing)
class IssueBookForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # We make 'book' optional (required=False) because they might type a name instead
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(quantity_available__gt=0),
        required=False, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # New field for manual entry
    manual_book_title = forms.CharField(
        required=False, 
        label="OR Type Book Name (If not in list)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. New History Book'})
    )

    class Meta:
        model = BorrowRecord
        fields = ['student', 'book', 'manual_book_title', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        book = cleaned_data.get('book')
        manual_title = cleaned_data.get('manual_book_title')

        # Logic: Either pick a book OR type a name, not both/neither
        if not book and not manual_title:
            raise forms.ValidationError("You must either select a book OR type a new book name.")
        return cleaned_data        