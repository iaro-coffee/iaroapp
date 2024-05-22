import os
import sys
import random

# Add the project directory to the sys.path
sys.path.append('/home/imme-deb-mac/Desktop/iaro-project/iaroapp')

# Set the environment variable for Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iaroapp.settings')

# Setup Django
import django
django.setup()

from tasks.models import Task, Weekdays, TaskTypes
from inventory.models import Branch
from django.contrib.auth import get_user_model

def create_mock_data(num_tasks):
    User = get_user_model()
    user = User.objects.first()
    branches = list(Branch.objects.all())
    weekdays = Weekdays.objects.all()
    task_types = TaskTypes.objects.all()

    for i in range(num_tasks):
        task = Task(
            title=f'Task {i}',
            summary=f'Task summary {i}',
        )
        task.save()
        task.weekdays.set(random.sample(list(weekdays), k=random.randint(0, len(weekdays))))
        task.users.add(user)
        task.groups.set(user.groups.all())
        task.branch.set(random.sample(branches, k=random.randint(1, len(branches))))
        task.types.set(random.sample(list(task_types), k=random.randint(1, len(task_types))))
        task.save()

# Create 1000 mock tasks
create_mock_data(8000)
print("Mock data created successfully")
