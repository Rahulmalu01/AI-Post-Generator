import os, openai, csv, requests
from dotenv import load_dotenv
from textblob import TextBlob

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import CaptionHistory, ImageHistory, UserProfile, SocialToken
from .forms import ProfileForm
from datetime import timedelta
from django.utils import timezone
from openai import OpenAI

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = response.data[0].url
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

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {'profile': profile})

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})

# OAuth Login
@login_required
def facebook_login(request):
    fb_auth_url = (
        f"https://www.facebook.com/v18.0/dialog/oauth?"
        f"client_id={os.getenv('FB_APP_ID')}"
        f"&redirect_uri={os.getenv('FB_REDIRECT_URI')}&scope=pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish"
    )
    return redirect(fb_auth_url)

# OAuth Callback
def facebook_callback(request):
    code = request.GET.get("code")
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"

    params = {
        "client_id": os.getenv("FB_APP_ID"),
        "redirect_uri": os.getenv("FB_REDIRECT_URI"),
        "client_secret": os.getenv("FB_APP_SECRET"),
        "code": code,
    }

    response = requests.get(token_url, params=params)
    tokens = response.json()
    short_token = tokens.get("access_token")

    # Step 2: Exchange for long-lived token
    exchange_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    exchange_params = {
        "grant_type": "fb_exchange_token",
        "client_id": os.getenv("FB_APP_ID"),
        "client_secret": os.getenv("FB_APP_SECRET"),
        "fb_exchange_token": short_token
    }
    long_res = requests.get(exchange_url, params=exchange_params)
    long_data = long_res.json()

    access_token = long_data.get("access_token")
    expires_in = long_data.get("expires_in", 60 * 60 * 24 * 60)  # default: 60 days

    if access_token:
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        SocialToken.objects.update_or_create(
            user=request.user,
            platform="facebook",
            defaults={
                "access_token": access_token,
                "expires_at": expires_at
            }
        )
        messages.success(request, "Facebook connected with long-lived token.")
    else:
        messages.error(request, f"Token exchange failed: {long_data}")

    return redirect("post_to_social")

# Helper functions
def get_page_id(access_token):
    response = requests.get("https://graph.facebook.com/me/accounts", params={"access_token": access_token})
    data = response.json()
    return data['data'][0]['id'] if data.get("data") else None

def get_ig_account_id(fb_page_id, access_token):
    url = f"https://graph.facebook.com/v18.0/{fb_page_id}?fields=instagram_business_account&access_token={access_token}"
    res = requests.get(url)
    return res.json().get("instagram_business_account", {}).get("id")

# Main Posting View
@login_required
@csrf_exempt
def post_to_social(request):
    token = SocialToken.objects.filter(user=request.user, platform="facebook").first()

    if not token:
        messages.error(request, "You must connect Facebook before posting.")
        return redirect('facebook_login')

    if token.expires_at and token.expires_at <= timezone.now():
        messages.error(request, "Your Facebook token has expired. Please reconnect.")
        return redirect('facebook_login')

    if request.method == 'POST':
        content = request.POST.get('content')
        platform = request.POST.get('platform')
        image_url = request.POST.get('image_url')
        access_token = token.access_token

        fb_page_id = get_page_id(access_token)

        if platform == "facebook":
            url = f"https://graph.facebook.com/{fb_page_id}/feed"
            payload = {"message": content, "access_token": access_token}
            res = requests.post(url, data=payload)
            if res.status_code in [200, 201]:
                messages.success(request, "Posted to Facebook Page.")
            else:
                messages.error(request, f"Facebook error: {res.text}")

        elif platform == "instagram":
            ig_id = get_ig_account_id(fb_page_id, access_token)
            if not ig_id:
                messages.error(request, "Instagram account not found.")
                return redirect('post_to_social')

            media_url = f"https://graph.facebook.com/v18.0/{ig_id}/media"
            media_res = requests.post(media_url, data={
                "image_url": image_url,
                "caption": content,
                "access_token": access_token
            })
            media_id = media_res.json().get("id")
            if not media_id:
                messages.error(request, f"Instagram media error: {media_res.text}")
                return redirect('post_to_social')

            publish_url = f"https://graph.facebook.com/v18.0/{ig_id}/media_publish"
            publish_res = requests.post(publish_url, data={
                "creation_id": media_id,
                "access_token": access_token
            })

            if publish_res.status_code in [200, 201]:
                messages.success(request, "Posted to Instagram.")
            else:
                messages.error(request, f"Instagram publish error: {publish_res.text}")

    return render(request, 'post_to_social.html', {'token': token})
