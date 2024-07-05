import livepopulartimes
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Fetches popular times data for a given place. "
        "The place_name argument should include the full address in the format: "
        '"location name, full address, city, province/state, country".'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "place_name",
            type=str,
            help="Name of the place to fetch data for, including the full address",
        )

    def handle(self, *args, **options):
        place_name = options["place_name"]
        formatted_address = place_name  # Assuming the full address is provided

        # Fetch data without API call
        data = livepopulartimes.get_populartimes_by_address(formatted_address)

        # Output all the fetched data to the console for inspection
        self.stdout.write(self.style.SUCCESS("Full Data:"))
        for key, value in data.items():
            self.stdout.write(self.style.SUCCESS(f"{key}: {value}"))
