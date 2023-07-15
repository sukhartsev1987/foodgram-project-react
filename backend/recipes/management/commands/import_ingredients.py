import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загрузка данных из файла backend/data/ingredients.csv"

    def handle(self, *args, **kwargs):
        try:
            if Ingredient.objects.exists():
                self.stdout.write("Данные уже загружены в базу данных.")
                return

            csv_file_path = "data/ingredients.csv"
            self._load_ingredients(csv_file_path)

            self.stdout.write("Данные успешно загружены в базу данных.")
        except FileNotFoundError:
            error_message = "Файл ingredients.csv не найден."
            self.stdout.write(self.style.ERROR(error_message))
        except Exception as e:
            error_message = f"Произошла ошибка: {str(e)}"
            self.stdout.write(self.style.ERROR(error_message))

    @staticmethod
    def _load_ingredients(csv_file_path):
        with open(csv_file_path, encoding="utf-8") as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader)
            for row in csvreader:
                Ingredient.objects.create(
                    name=row[0],
                    measurement_unit=row[1],
                )
