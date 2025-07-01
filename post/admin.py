from django.contrib import admin
from .models import CaptionHistory, ImageHistory, UserProfile

admin.site.register(CaptionHistory)
admin.site.register(ImageHistory)
admin.site.register(UserProfile)
