from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ContactMessage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from .models import UserExtra
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout
from .models import ProcessedDocument
import PyPDF2
from django.contrib.auth.decorators import login_required
import PyPDF2
import requests
import textwrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from django.db.models import Sum, Count
from django.contrib.auth import logout as auth_logout


OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-4o-mini"

# Create your views here.
def home(request):
    return render(request, 'home.html')

def features(request):
    return render(request, 'features.html')

def pricing(request):
    return render(request, 'pricing.html')

def contact(request):
    return render(request, 'contact.html')

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirect logged-in users

    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        # Try to authenticate by username
        user = authenticate(request, username=username_or_email, password=password)

        # If not found, try to authenticate by email
        if not user:
            from django.contrib.auth.models import User
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user:
            auth_login(request, user)
            if not remember:
                request.session.set_expiry(0)  # Session expires on browser close
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'login.html')

def sign(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        terms = request.POST.get('terms')

        # -----------------------
        # Validation
        # -----------------------
        if not all([full_name, email, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return render(request, 'sign.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'sign.html')

        if not terms:
            messages.error(request, "You must agree to the Terms & Privacy Policy.")
            return render(request, 'sign.html')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email address already in use.")
            return render(request, 'sign.html')

        # -----------------------
        # Create User
        # -----------------------
        try:
            username = email.split('@')[0]  # simple username generation
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = full_name
            user.save()

            # -----------------------
            # Create UserExtra
            # -----------------------
            UserExtra.objects.create(
                user=user,
                full_name=full_name,
                total_pdfs_processed=0,
                total_words_processed=0,
                total_pages_processed=0,
                total_points_earned=0,
            )

            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')  # replace 'login' with your login url name

        except IntegrityError:
            messages.error(request, "An error occurred while creating your account. Try again.")
            return render(request, 'sign.html')

    # GET request
    return render(request, 'sign.html')



def custom_logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

def about(request):
    return render(request, 'about.html')

def policy(request):
    return render(request, 'policy.html')

def terms(request):
    return render(request, 'terms.html')

@login_required
def dashboard(request):
    user_extra, created = UserExtra.objects.get_or_create(user=request.user)

    # Fetch recent PDFs
    recent_docs = ProcessedDocument.objects.filter(
        user=request.user,
        deleted_by_user=False
    ).order_by('-created_at')[:10]

    # Prepare recent PDFs data for template
    recent_pdfs = []
    for doc in recent_docs:
        recent_pdfs.append({
            "id": doc.id,
            "name": doc.pdf_file.name.split('/')[-1],
            "uploaded_at": doc.created_at,
            "status": "Processed" if doc.processed_count > 0 else "Not Processed",
            "download_url": doc.pdf_file.url,
            "generated_pdf_url": doc.generated_pdf.url if doc.generated_pdf else None
        })

    context = {
        "user_extra": user_extra,
        "total_pdfs": user_extra.total_pdfs_processed,
        "points_earned": user_extra.total_points_earned,
        "total_words": user_extra.total_words_processed,
        "total_pages": user_extra.total_pages_processed,
        "recent_pdfs": recent_pdfs,
        "top_topics": "Math, Science, English",  # Example placeholder, can be dynamic
        "questions_generated": 0,  # Can calculate based on generated PDFs
        "time_saved": 0,           # Can calculate based on processing speed
    }

    return render(request, "dashboard.html", context)


@login_required
def upload_pdf(request):

    # -----------------------------
    # Handle Delete Request
    # -----------------------------
    if request.method == "POST" and "delete_id" in request.POST:
        doc_id = request.POST.get("delete_id")
        try:
            doc = ProcessedDocument.objects.get(id=doc_id, user=request.user)
            doc.deleted_by_user = True  # Make sure this field exists in your model
            doc.save()
            messages.success(request, "Document deleted successfully.")
        except ProcessedDocument.DoesNotExist:
            messages.error(request, "Document not found.")
        return redirect("upload_pdf")

    # -----------------------------
    # Handle PDF Upload
    # -----------------------------
    if request.method == "POST" and "pdf_file" in request.FILES:
        pdf_file = request.FILES.get("pdf_file")

        if not pdf_file:
            messages.error(request, "Please upload a PDF file.")
            return redirect("upload_pdf")

        # Save new document
        document = ProcessedDocument(user=request.user, pdf_file=pdf_file)
        document.save()

        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)
            num_words = sum(
                len(page.extract_text().split()) for page in pdf_reader.pages if page.extract_text()
            )

            document.num_pages = num_pages
            document.num_words = num_words
            document.processed_count = 0  # Set to 0; you can increment after actual processing
            document.save()

            messages.success(request, f"PDF uploaded successfully! Pages: {num_pages}, Words: {num_words}")

        except Exception as e:
            messages.error(request, f"Error processing PDF: {str(e)}")

        # Refresh the documents queryset so the new file appears
        user_documents = ProcessedDocument.objects.filter(
            user=request.user,
            deleted_by_user=False
        ).order_by("-created_at")

        return render(request, "upload_pdf.html", {"documents": user_documents})

    # -----------------------------
    # Render Page (GET Request)
    # -----------------------------
    user_documents = ProcessedDocument.objects.filter(
        user=request.user,
        deleted_by_user=False
    ).order_by("-created_at")

    return render(request, "upload_pdf.html", {"documents": user_documents})





def subscription(request):
    return render(request, 'subscription.html')


def send_contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        # Basic backend validation
        if not name or not email or not subject or not message:
            messages.error(request, "Please complete all required fields.")
            return redirect("/contact/")

        # Save to database
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        # Success message
        messages.success(request, "Thank you! Your message has been sent successfully.")
        return redirect("/contact/")

    return render(request, "contact.html")



# ----------------------------------------------------------------------
# PROCESS SELECTED PDF
# ----------------------------------------------------------------------

@login_required
def process_selected(request, doc_id):
    if not OPENROUTER_API_KEY:
        messages.error(request, "Server misconfiguration: OpenRouter API key is missing.")
        return redirect("upload_pdf")

    # Fetch document
    document = get_object_or_404(
        ProcessedDocument,
        id=doc_id,
        user=request.user,
        deleted_by_user=False
    )

    # -------------------------------
    # Check subscription & limits
    # -------------------------------
    user_extra, _ = UserExtra.objects.get_or_create(user=request.user)
    now = timezone.now()

    if not user_extra.subscription_active or (user_extra.subscription_end and user_extra.subscription_end < now):
        messages.error(request, "Your subscription has expired or is inactive. Please renew to process documents.")
        return redirect("settings_page")

    if user_extra.plan == 'free':
        today_count = ProcessedDocument.objects.filter(
            user=request.user,
            created_at__date=now.date(),
            deleted_by_user=False
        ).count()
        if today_count >= 2:
            messages.error(request, "Free plan users can process a maximum of 2 documents per day. Upgrade to Pro for unlimited access.")
            return redirect("settings_page")

    pdf_path = document.pdf_file.path

    # -------------------------------
    # Step 1: Read PDF
    # -------------------------------
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        text_content = "\n".join(page.extract_text() or "" for page in reader.pages)

        if not text_content.strip():
            messages.error(request, "Could not extract text from PDF.")
            return redirect("upload_pdf")

        # Update document stats
        document.num_words = len(text_content.split())
        document.num_pages = len(reader.pages)
        document.processed_count += 1
        document.save()

        # Update user stats
        user_extra.total_pdfs_processed += 1
        user_extra.total_words_processed += document.num_words
        user_extra.total_pages_processed += document.num_pages
        user_extra.total_points_earned += document.num_words // 100
        user_extra.save()

    except Exception as e:
        messages.error(request, f"PDF processing error: {e}")
        return redirect("upload_pdf")

    # -------------------------------
    # Step 2: Split text into chunks
    # -------------------------------
    def split_text(txt, max_words=800):
        words = txt.split()
        for i in range(0, len(words), max_words):
            yield " ".join(words[i:i + max_words])

    chunks = list(split_text(text_content, max_words=800))

    # -------------------------------
    # Step 3: Call OpenRouter API
    # -------------------------------
    all_generated_text = ""
    for idx, chunk in enumerate(chunks, start=1):
        prompt = f"""
        
You are an AI assistant. Summarize the following text into roughly one-third of its length and generate questions that cover all key aspects.

Text:
{chunk}

Tasks:
Summarize the content into one cohesive paragraph equal to roughly one-third of the total length. Begin immediately with the core ideas—avoid phrases such as “in this text,” “in this passage,” or any similar reference. Use clean, professional language. Do not use special characters or decorative symbols such as #, *, -, or similar. Present the summary under a clear heading such as Summary, Key Insights, or Main Overview.

After the summary, extract the essential ideas and present them concisely under a heading titled Main Points. List them in clear standalone lines without numbering or bullet symbols.

Next, generate questions that test reasoning, relationships, cause and effect, conceptual understanding, and implications. Avoid shallow prompts like “What is the topic?” or “What is the title?”. Create three categories of questions:

Fill-in-the-blank questions
True or False questions
Comprehension questions that require meaningful interpretation

Each category must be presented under its own heading, and each question must appear on a separate line without numbers or bullet points.

Place each question on a new line. Keep the output clean and professional.

Format the response clearly.
Formatting Rules:
1. Each category must have its own heading exactly matching the names above.
2. Number every question using standard numbering (1., 2., 3., etc.).
3. Each question must appear on a separate line.
4. Place a line break before every question by inserting the newline character "\n".
5. Do not combine multiple questions on the same line.
6. Do not include decorative characters, symbols, or markdown formatting.
7. The final output must strictly follow the structure:
8. Summary → Main Points → Fill-in-the-Blank Questions → True or False Questions → Comprehension Questions.
9. Place a line break after every heading by inserting the newline character ": \n".
10. Place a line break before every point in the main points by inserting the newline character "\n", also add a bullet before each point.

        """

        try:
            response = requests.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                timeout=60
            )
            response.raise_for_status()
            generated_text = response.json()['choices'][0]['message']['content']
            all_generated_text += f"\n\n--- Part {idx} ---\n\n{generated_text}"

        except requests.exceptions.RequestException as e:
            messages.error(request, f"OpenRouter API error: {e}")
            return redirect("upload_pdf")
        except KeyError:
            messages.error(request, "Unexpected API response format.")
            return redirect("upload_pdf")

    # -------------------------------
    # Step 4: Save Generated PDF
    # -------------------------------
    output_dir = "media/generated_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    output_name = f"processed_{document.id}.pdf"
    output_path = os.path.join(output_dir, output_name)

    c = canvas.Canvas(output_path, pagesize=letter)
    x_margin, y_margin = 50, 12
    line_height = 14
    y = 750

    wrapper = textwrap.TextWrapper(width=95)
    for paragraph in all_generated_text.split("\n\n"):
        for line in wrapper.wrap(paragraph):
            if y < 50:
                c.showPage()
                y = 750
            c.drawString(x_margin, y, line)
            y -= line_height
        y -= line_height

    c.save()

    document.generated_pdf.name = f"generated_pdfs/{output_name}"
    document.save()

    messages.success(request, "Processing complete! Download available.")
    return redirect("upload_pdf")



@login_required(login_url='/login/')
def settings_page(request):
    user = request.user

    # Get or create extra user info
    user_extra, _ = UserExtra.objects.get_or_create(user=user)

    # Count PDFs and related stats
    pdf_qs = ProcessedDocument.objects.filter(user=user, deleted_by_user=False)
    total_pdfs = pdf_qs.count()
    total_words = pdf_qs.aggregate(total_words=Sum('num_words'))['total_words'] or 0
    total_pages = pdf_qs.aggregate(total_pages=Sum('num_pages'))['total_pages'] or 0
    generated_pdfs_count = pdf_qs.filter(generated_pdf__isnull=False).count()

    context = {
        'user': user,
        'user_extra': user_extra,
        'total_pdfs': total_pdfs,
        'total_words': total_words,
        'total_pages': total_pages,
        'generated_pdfs_count': generated_pdfs_count,
    }


    return render(request, 'settings.html', context)


