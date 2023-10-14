from math import floor

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum, Avg
from django.forms import model_to_dict

from ratings.models import EmployeeRating
from django.http import HttpResponse
import json
import datetime
from django.shortcuts import render


# Tip input page
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
            rating = floor(rating * 100) / 100.0
        userDicts.append({'user': model_to_dict(user), 'avg_rating': rating})
    return render(
        request,
        'ratings_evaluation.html',
        context={
            'list': userDicts,
        },
    )
