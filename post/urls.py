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
]
