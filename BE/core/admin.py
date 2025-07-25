from django.contrib import admin

# Note: MongoEngine models cannot be registered with Django admin
# Use Django admin only for Django ORM models (User, etc.)
# For MongoEngine models, consider using a custom admin interface or API endpoints 