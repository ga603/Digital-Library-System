import csv
import io
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, BorrowRecord, User, Student, Category
from datetime import date
from django.db.models import Sum
from .forms import IssueBookForm, StudentRegistrationForm, CSVUploadForm

@login_required
def index(request):
    # 1. Counts (Existing code)
    num_books = Book.objects.count()
    num_instances_available = Book.objects.filter(quantity_available__gt=0).count()
    num_issued = BorrowRecord.objects.filter(status='ISSUED').count()
    num_overdue = BorrowRecord.objects.filter(status='ISSUED', due_date__lt=date.today()).count()
    
    # 2. NEW: Fetch last 5 transactions (Newest first)
    recent_transactions = BorrowRecord.objects.all().order_by('-issue_date', '-id')[:5]

    context = {
        'num_books': num_books,
        'num_instances_available': num_instances_available,
        'num_issued': num_issued,
        'num_overdue': num_overdue,
        'recent_transactions': recent_transactions, # Pass it to the template
    }

    return render(request, 'catalog/index.html', context=context)

@login_required
def book_list(request):
    query = request.GET.get('q') # Get the search term from the URL
    if query:
        # Search by title OR author OR isbn
        books = Book.objects.filter(
            Q(title__icontains=query) | 
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )
    else:
        books = Book.objects.all()

    context = {
        'books': books,
        'search_term': query if query else ''
    }
    return render(request, 'catalog/book_list.html', context)
from django.shortcuts import redirect
from django.contrib import messages
from .forms import IssueBookForm # Import the form we just made

# ... existing views ...

@login_required
def issue_book(request):
    if request.method == 'POST':
        form = IssueBookForm(request.POST)
        if form.is_valid():
            # 1. Don't save to DB yet (commit=False)
            borrow_record = form.save(commit=False)
            
            # 2. Get the book instance
            book = borrow_record.book
            
            # 3. Double check availability (Safety net)
            if book.quantity_available > 0:
                # 4. Decrease quantity
                book.quantity_available -= 1
                book.save()
                
                # 5. Save the record
                borrow_record.save()
                messages.success(request, f"Book '{book.title}' issued to {borrow_record.student.username}")
                return redirect('index') # Redirect to Dashboard
            else:
                messages.error(request, "This book is currently out of stock!")
    else:
        form = IssueBookForm()

    return render(request, 'catalog/issue_book.html', {'form': form})

@login_required
def active_loans(request):
    # Only get records that are 'ISSUED'
    loans = BorrowRecord.objects.filter(status='ISSUED').order_by('due_date')
    return render(request, 'catalog/active_loans.html', {'loans': loans})

# 3. View to PROCESS the return

@login_required
def return_book_action(request, pk):
    # Get the specific record by its Primary Key (pk)
    record = get_object_or_404(BorrowRecord, pk=pk)
    
    if record.status == 'ISSUED':
        # A. Mark as Returned
        record.status = 'RETURNED'
        record.return_date = date.today()
        record.save()
        
        # B. Increase Book Inventory
        book = record.book
        book.quantity_available += 1
        book.save()
        
        # C. Calculate Fine
        fine = record.calculate_fine()
        
        if fine > 0:
            messages.warning(request, f"Book Returned. LATE FINE: {fine} KES")
        else:
            messages.success(request, f"Book '{book.title}' returned successfully.")
            
    return redirect('active_loans')

@login_required
def add_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            student = form.save() # Just save it! No passwords, no roles.
            messages.success(request, f"Student '{student.first_name}' added to the registry!")
            return redirect('issue_book')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'catalog/add_student.html', {'form': form})
@login_required
def upload_books(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Decode file (convert bytes to string)
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            next(io_string) # Skip the header row
            
            for column in csv.reader(io_string, delimiter=',', quotechar='"'):
                # FORMAT: Title, Author, ISBN, Category, Quantity
                # Example: Math Form 4, KLB, 999222, Mathematics, 10
                try:
                    # Get or Create Category
                    category_obj, created = Category.objects.get_or_create(name=column[3])
                    
                    # Create Book
                    Book.objects.create(
                        title=column[0],
                        author=column[1],
                        isbn=column[2],
                        category=category_obj,
                        quantity_total=int(column[4]),
                        quantity_available=int(column[4])
                    )
                except Exception as e:
                    print(f"Skipping row: {e}")
            
            messages.success(request, "Books uploaded successfully!")
            return redirect('index')
    else:
        form = CSVUploadForm()
        
    return render(request, 'catalog/upload_books.html', {'form': form})

# 2. UPDATE VIEW: Issue Book (Smart Logic)
@login_required
def issue_book(request):
    if request.method == 'POST':
        form = IssueBookForm(request.POST)
        if form.is_valid():
            borrow_record = form.save(commit=False)
            
            # --- SMART LOGIC START ---
            manual_title = form.cleaned_data.get('manual_book_title')
            
            if manual_title:
                # 1. Create a dummy category for manual books
                cat, _ = Category.objects.get_or_create(name="Manually Added")
                
                # 2. Create the new book on the fly
                # Use a random number for ISBN since we don't have one
                import random
                new_book = Book.objects.create(
                    title=manual_title,
                    author="Unknown",
                    isbn=str(random.randint(10000000, 99999999)), 
                    category=cat,
                    quantity_total=1,
                    quantity_available=0 # 0 because we are issuing it right now!
                )
                borrow_record.book = new_book
                messages.warning(request, f"New book '{manual_title}' was created and added to the system.")
            else:
                # Normal process
                book = borrow_record.book
                if book.quantity_available > 0:
                    book.quantity_available -= 1
                    book.save()
                else:
                    messages.error(request, "Book out of stock!")
                    return redirect('issue_book')
            # --- SMART LOGIC END ---

            borrow_record.save()
            messages.success(request, f"Book issued to {borrow_record.student.first_name}!")
            return redirect('index')
    else:
        form = IssueBookForm()

    return render(request, 'catalog/issue_book.html', {'form': form})
# ... existing imports ...

@login_required
def student_history(request, pk):
    # 1. Get the specific student by their ID (Primary Key)
    student = get_object_or_404(Student, pk=pk)
    
    # 2. Get all borrowing history for this student (Newest first)
    history = BorrowRecord.objects.filter(student=student).order_by('-issue_date')
    
    # 3. Check if they have any active overdue books
    has_overdue = False
    for record in history:
        if record.status == 'ISSUED' and record.calculate_fine() > 0:
            has_overdue = True
            break

    context = {
        'student': student,
        'history': history,
        'has_overdue': has_overdue
    }
    return render(request, 'catalog/student_history.html', context)
@login_required
def student_list(request):
    query = request.GET.get('q') # Search term from the search bar
    
    if query:
        # Search by First Name, Last Name, OR Admission Number
        students = Student.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(admission_number__icontains=query)
        )
    else:
        students = Student.objects.all().order_by('student_class', 'first_name')

    return render(request, 'catalog/student_list.html', {'students': students, 'search_term': query})

def landing_page(request):
    return render(request, 'catalog/landing.html')
