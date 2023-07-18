import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        if Ingredient.objects.exists():
            self.stdout.write("Данные были загружены ранее.")
            return
        path_csv = "data/ingredients.csv"
        self._import_ingredients(path_csv)
        self.stdout.write("Данные успешно загружены.")

    @staticmethod
    def _import_ingredients(path_csv):
        with open(path_csv, encoding="utf-8") as csvfile:
            reader_csv = csv.reader(csvfile)
            next(reader_csv)
            for row in reader_csv:
                Ingredient.objects.create(
                    name=row[0],
                    measurement_unit=row[1]
                )
