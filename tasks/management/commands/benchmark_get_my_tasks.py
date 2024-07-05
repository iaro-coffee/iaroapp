# tasks/management/commands/benchmark_get_my_tasks.py

import os

import django
from django.core.management.base import BaseCommand

# Set the environment variable for Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iaroapp.settings")

# Setup Django
django.setup()


class Command(BaseCommand):
    help = "Benchmark get_my_tasks functions"

    def handle(self, *args, **kwargs):
        from tasks.bench import benchmark_get_my_tasks  # Import the function here

        # Assuming you have a way to get a mock or real request object for testing
        request = self.get_request_object()
        combined_duration, separated_duration = benchmark_get_my_tasks(request)

        self.stdout.write(
            self.style.SUCCESS(f"Combined Query Duration: {combined_duration}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Separated Query Duration: {separated_duration}")
        )

    def get_request_object(self):
        # Mock or create a request object for testing purposes
        pass
