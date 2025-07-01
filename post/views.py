import os, replicate, openai, csv
from dotenv import load_dotenv
from textblob import TextBlob

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import CaptionHistory, ImageHistory

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

def index(request):
    return render(request, 'index.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Account created. Please sign in.")
        return redirect('signin')
    return render(request, 'signup.html')

def signin(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, "Invalid credentials.")
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
    return render(request, 'signin.html')

def logout_view(request):
    logout(request)
    return redirect('signin')

@login_required
def generate_caption(request):
    if request.method == 'POST':
        topic = request.POST.get('topic', '')
        if not topic:
            return JsonResponse({'error': 'No topic provided'}, status=400)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate catchy, brand-friendly captions for social media."},
                    {"role": "user", "content": f"Generate a caption for: {topic}"}
                ]
            )
            caption = response.choices[0].message['content'].strip()
            CaptionHistory.objects.create(user=request.user, caption=caption)
            return JsonResponse({'caption': caption})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=405)

@login_required
def generate_image(request):
    if request.method == 'POST':
        prompt = request.POST.get('prompt', '')
        if not prompt:
            return JsonResponse({'error': 'No prompt provided'}, status=400)
        try:
            replicate_client = replicate.Client(api_token=REPLICATE_API_TOKEN)
            output = replicate_client.run(
                "stability-ai/sdxl:latest",
                input={"prompt": prompt}
            )
            image_url = output[0]
            ImageHistory.objects.create(user=request.user, prompt=prompt, image_url=image_url)
            return JsonResponse({'image_url': image_url})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=405)

@login_required
def predict_engagement(request):
    if request.method == 'POST':
        caption = request.POST.get('caption', '')
        if not caption:
            return JsonResponse({'error': 'No caption provided'}, status=400)
        try:
            polarity = TextBlob(caption).sentiment.polarity
            length = len(caption)
            likes = int(100 + (polarity * 100) + (length / 2))
            shares = int(20 + (polarity * 40) + (length / 10))
            return JsonResponse({'likes': likes, 'shares': shares})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=405)

@login_required
def dashboard(request):
    captions = CaptionHistory.objects.filter(user=request.user).order_by('-generated_at')
    images = ImageHistory.objects.filter(user=request.user).order_by('-generated_at')
    return render(request, 'dashboard.html', {'captions': captions, 'images': images})

@login_required
def export_captions_csv(request):
    captions = CaptionHistory.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=captions.csv'

    writer = csv.writer(response)
    writer.writerow(['Caption', 'Generated At'])
    for c in captions:
        writer.writerow([c.caption, c.generated_at])

    return response

@login_required
def export_images_csv(request):
    images = ImageHistory.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=images.csv'

    writer = csv.writer(response)
    writer.writerow(['Prompt', 'Image URL', 'Generated At'])
    for i in images:
        writer.writerow([i.prompt, i.image_url, i.generated_at])

    return response
