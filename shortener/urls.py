from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("api/shorten/", views.api_shorten, name="api_shorten"),
    path("api/urls/", views.api_list, name="api_list"),

    # Specific analytics routes must come first
    path(
        "api/analytics/summary/",
        views.api_analytics_summary,
        name="api_analytics_summary"
    ),
    path(
        "api/analytics/activity/",
        views.api_click_activity,
        name="api_click_activity"
    ),

    # Dynamic route must come after specific routes
    path(
        "api/analytics/<str:code>/",
        views.api_url_analytics,
        name="api_url_analytics"
    ),

    # Keep the general redirect route last
    path("<str:code>/", views.redirect_url, name="redirect_url"),
]