from django.shortcuts import render

# Create your views here.
import string
import random

from django.shortcuts import render, redirect, get_object_or_404
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db.models import F

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import ShortURLSerializer
from django.core.cache import cache
from .models import ShortURL, URLClick
from django.db.models import Sum

from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone

from .models import ShortURL


def generate_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def home(request):
    short_url = None
    error = None

    if request.method == "POST":
        original_url = request.POST.get("original_url", "").strip()
        validator = URLValidator()

        try:
            validator(original_url)

            code = generate_code()

            while ShortURL.objects.filter(short_code=code).exists():
                code = generate_code()

            url = ShortURL.objects.create(
                original_url=original_url,
                short_code=code
            )

            short_url = request.build_absolute_uri(
                f"/{url.short_code}/"
            )

        except ValidationError:
            error = "Please enter a valid URL."

    urls = ShortURL.objects.all().order_by("-created_at")

    return render(request, "shortener/home.html", {
        "short_url": short_url,
        "error": error,
        "urls": urls,
    })



def redirect_url(request, code):
    cache_key = f"shorturl:{code}"
    original_url = cache.get(cache_key)

    if original_url is None:
        url = get_object_or_404(ShortURL, short_code=code)
        original_url = url.original_url
        cache.set(cache_key, original_url, timeout=3600)

    ShortURL.objects.filter(
        short_code=code
    ).update(clicks=F("clicks") + 1)

    URLClick.objects.create(
        short_url=ShortURL.objects.get(short_code=code)
    )

    return redirect(original_url)

@api_view(["POST"])
def api_shorten(request):
    serializer = ShortURLSerializer(data=request.data)

    if serializer.is_valid():
        code = generate_code()

        while ShortURL.objects.filter(short_code=code).exists():
            code = generate_code()

        url = serializer.save(short_code=code)

        short_url = request.build_absolute_uri(
            f"/{url.short_code}/"
        )

        return Response({
            "id": url.id,
            "original_url": url.original_url,
            "short_code": url.short_code,
            "short_url": short_url,
            "clicks": url.clicks,
        }, status=status.HTTP_201_CREATED)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["GET"])
def api_list(request):
    urls = ShortURL.objects.all().order_by("-created_at")
    serializer = ShortURLSerializer(urls, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def api_url_analytics(request, code):
    url = get_object_or_404(ShortURL, short_code=code)

    click_events = url.click_events.order_by("clicked_at")

    return Response({
        "short_code": url.short_code,
        "original_url": url.original_url,
        "total_clicks": url.clicks,
        "click_events": [
            {
                "clicked_at": event.clicked_at
            }
            for event in click_events
        ]
    })



@api_view(["GET"])
def api_analytics_summary(request):
    total_urls = ShortURL.objects.count()

    total_clicks = ShortURL.objects.aggregate(
        total=Sum("clicks")
    )["total"] or 0

    most_clicked = ShortURL.objects.order_by(
        "-clicks"
    ).first()

    return Response({
        "total_urls": total_urls,
        "total_clicks": total_clicks,
        "most_clicked_url": {
            "short_code": most_clicked.short_code,
            "original_url": most_clicked.original_url,
            "clicks": most_clicked.clicks
        } if most_clicked else None
    })


@api_view(["GET"])
def api_click_activity(request):
    since = timezone.now() - timedelta(days=7)

    activity = (
        URLClick.objects
        .filter(clicked_at__gte=since)
        .annotate(day=TruncDate("clicked_at"))
        .values("day")
        .annotate(clicks=Count("id"))
        .order_by("day")
    )

    return Response([
        {
            "date": item["day"].isoformat(),
            "clicks": item["clicks"]
        }
        for item in activity
    ])

