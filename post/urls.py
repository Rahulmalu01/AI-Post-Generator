from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('generate-caption/', views.generate_caption, name='generate_caption'),
    path('generate-image/', views.generate_image, name='generate_image'),
    path('predict-engagement/', views.predict_engagement, name='predict_engagement'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export/captions/', views.export_captions_csv, name='export_captions'),
    path('export/images/', views.export_images_csv, name='export_images'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('post-to-social/', views.post_to_social, name='post_to_social'),

    # 🔗 Facebook & Instagram OAuth and callback
    path('facebook/login/', views.facebook_login, name='facebook_login'),
    path('facebook/callback/', views.facebook_callback, name='facebook_callback'),
]
