from math import floor

from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Avg
from django.forms import model_to_dict

from ratings.models import EmployeeRating
from django.http import HttpResponse
import json
import datetime
from django.shortcuts import render


@login_required
def index(request):
    if request.method == 'POST':
        request_data = request.body
        form_data = json.loads(request_data.decode("utf-8"))
        for user_id, value in form_data.items():
            star = value['star']
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
    userDicts = []
    for user in users:
        rating = EmployeeRating.objects.filter(user=user).aggregate(Avg('rating'))['rating__avg']
        if (rating):
            rating = floor(rating * 10) / 10.0
        userDicts.append({'user': model_to_dict(user), 'avg_rating': rating})
    return render(
        request,
        'ratings_evaluation.html',
        context={
            'list': userDicts,
        },
    )

@user_passes_test(check_admin)
def user_ratings_evaluation(request, id):
    userName = User.objects.filter(id=id).distinct().values('username')[0]['username']
    userRatings = []
    avgRating = EmployeeRating.objects.filter(user=id).aggregate(Avg('rating'))['rating__avg']
    if avgRating:
        avgRating = floor(avgRating*10)/10.0
    ratings = EmployeeRating.objects.filter(user=id).order_by('date').reverse()
    for rating in ratings:
        userRatings.append(model_to_dict(rating))

    return render(
        request,
        'user_ratings_evaluation.html',
        context={
            'ratings': userRatings,
            'avgRating': avgRating,
            'userName': userName,
        },
    )
