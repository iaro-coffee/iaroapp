import datetime
import json
from math import floor

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render

from ratings.models import EmployeeRating


@login_required
def index(request):
    if request.method == "POST":
        request_data = request.body
        form_data = json.loads(request_data.decode("utf-8"))
        for user_id, value in form_data.items():
            star = value["star"]
            user = User.objects.get(id=user_id)
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # add star
            EmployeeRating.objects.create(user=user, rating=star, date=date)
        return HttpResponse(200)
    return


def check_admin(user):
    return user.is_superuser


@user_passes_test(check_admin)
def ratings_evaluation(request):
    users = User.objects.all()

    teamRatings = {
        "dates": [],
        "ratings": [],
    }
    teamRatingsQuerySet = (
        EmployeeRating.objects.filter()
        .values("date__date")
        .annotate(average=Avg("rating"))
        .order_by("-date__date")[:15]
    )

    for result in teamRatingsQuerySet.iterator():
        teamRatings["dates"].insert(0, result["date__date"])
        teamRatings["ratings"].insert(0, result["average"])

    userDicts = []
    for user in users:
        rating = EmployeeRating.objects.filter(user=user).aggregate(Avg("rating"))[
            "rating__avg"
        ]
        if rating:
            rating = floor(rating * 10) / 10.0
            ratingBar = int(round(rating / 5 * 100, -1))
        else:
            rating = 0
            ratingBar = 0

        try:
            profile = user.profile  # check profile to avoid RelatedObject not found
            userDicts.append(
                {
                    "user": model_to_dict(user),
                    "profile": model_to_dict(profile),
                    "avg_rating": rating,
                    "avg_rating_bar": ratingBar,
                }
            )
        except User.profile.RelatedObjectDoesNotExist:
            userDicts.append(
                {
                    "user": model_to_dict(user),
                    "profile": None,
                    "avg_rating": rating,
                    "avg_rating_bar": ratingBar,
                }
            )

    userDicts.sort(key=lambda x: (x["avg_rating"] == 0, x["avg_rating"]), reverse=False)
    return render(
        request,
        "ratings_evaluation.html",
        context={
            "pageTitle": "Ratings overview",
            "list": userDicts,
            "teamRatings": teamRatings,
        },
    )


@user_passes_test(check_admin)
def user_ratings_evaluation(request, id):
    userName = User.objects.filter(id=id).distinct().values("username")[0]["username"]
    avgRating = EmployeeRating.objects.filter(user=id).aggregate(Avg("rating"))[
        "rating__avg"
    ]
    if avgRating:
        avgRating = floor(avgRating * 10) / 10.0

    userRatings = {
        "dates": [],
        "ratings": [],
    }
    ratings = (
        EmployeeRating.objects.filter(user=id)
        .values("date__date", "rating")
        .order_by("-date")[:25]
    )

    for result in ratings.iterator():
        userRatings["dates"].insert(0, result["date__date"])
        userRatings["ratings"].insert(0, result["rating"])

    return render(
        request,
        "user_ratings_evaluation.html",
        context={
            "pageTitle": "Ratings from " + userName + " (∅ " + str(avgRating) + ")",
            "userRatings": userRatings,
            "avgRating": avgRating,
            "userName": userName,
        },
    )
