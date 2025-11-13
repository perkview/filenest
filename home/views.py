from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse
from .models import Document

# Create your views here.
def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('landing_page')
        else:
            return render(request, 'auth.html', {'error_login': 'Invalid email or password'})
    return redirect('auth_page')

def signup_user(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            return render(request, 'auth.html', {'error_signup': 'Passwords do not match'})
        if User.objects.filter(username=email).exists():
            return render(request, 'auth.html', {'error_signup': 'Email address already in use'})

        user = User.objects.create_user(username=email, email=email, password=password1, first_name=name)
        user.save()
        return redirect('auth_page')

    return redirect('auth_page')


def dashboard_page(request):
    # Example context
    stats = {
        'documents_count': 12,
        'tokens_used': 3450,
        'active_users': 8,
        'recent_activity_count': 5,
    }

    recent_documents = [
        {'id': 1, 'filename': 'ProjectPlan.pdf', 'pages': 12, 'size_bytes': 256000, 'upload_ts': '2025-11-13 10:00', 'status': 'processed'},
        {'id': 2, 'filename': 'MeetingNotes.docx', 'pages': 5, 'size_bytes': 54000, 'upload_ts': '2025-11-12 14:30', 'status': 'pending'},
    ]

    return render(request, 'dashboard.html', {
        'stats': stats,
        'recent_documents': recent_documents
    })

def upload_page(request):
    if request.method == 'POST' and request.FILES.get('document'):
        uploaded_file = request.FILES['document']
        doc = Document.objects.create(
            owner=request.user,
            filename=uploaded_file.name,
            file=uploaded_file,
            size_bytes=uploaded_file.size,
        )
        return render(request, 'upload.html', {'success': True, 'uploaded_file_name': doc.filename})
    return render(request, 'upload.html')

def view_document(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)
    return render(request, 'view_document.html', {'document': document})

def download_document(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)
    # Assuming your file field is `file` in Document model
    response = FileResponse(document.file.open('rb'), as_attachment=True, filename=document.filename)
    return response

def home(request):
    return render(request, 'home.html')

def auth_page(request):
    return render(request, 'auth.html')

def features_page(request):
    return render(request, 'features.html')

# How It Works page
def how_it_works(request):
    return render(request, 'how_it_works.html')

# Security page
def security(request):
    return render(request, 'security.html')

# Pricing page
def pricing(request):
    return render(request, 'pricing.html')

def profile(request):
    return render(request, 'profile.html')

def settings(request):
    return render(request, 'settings.html')