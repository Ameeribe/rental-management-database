import csv
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


VIEW_DROP_ORDER = [
    "ProblematicRenters",
    "RepeatedRoommates",
    "Roommates",
    "maskir_minimalist",
    "sokhir_minimalist",
    "few_years_apts",
    "good_owners",
    "rent_ok",
]
TABLE_DROP_ORDER = ["Rentals", "Apartments", "Owners"]


def sql_batches(path):
    """Split a SQL Server script on client-side GO batch separators."""
    source = path.read_text(encoding="utf-8")
    return [
        batch.strip()
        for batch in re.split(r"(?im)^\s*GO\s*$", source)
        if batch.strip()
    ]


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


class Command(BaseCommand):
    help = "Create the rental schema, load sample CSV data, and create SQL views."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Drop existing portfolio views and tables before rebuilding them.",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        schema_path = base_dir / "sql" / "schema.sql"
        views_path = base_dir / "sql" / "views.sql"
        data_dir = base_dir / "data"

        if not all(path.exists() for path in (schema_path, views_path, data_dir)):
            raise CommandError("The sql/ or data/ setup files are missing.")

        with transaction.atomic(), connection.cursor() as cursor:
            if options["reset"]:
                for view_name in VIEW_DROP_ORDER:
                    cursor.execute(f"DROP VIEW IF EXISTS [{view_name}]")
                for table_name in TABLE_DROP_ORDER:
                    cursor.execute(f"DROP TABLE IF EXISTS [{table_name}]")
            else:
                cursor.execute("SELECT OBJECT_ID('dbo.Owners', 'U')")
                if cursor.fetchone()[0] is not None:
                    raise CommandError(
                        "The sample schema already exists. Use --reset to rebuild it."
                    )

            for batch in sql_batches(schema_path):
                cursor.execute(batch)

            owners = list(csv_rows(data_dir / "Owners.csv"))
            cursor.executemany(
                """
                INSERT INTO Owners (ownerID, oName, residenceCity, bDate)
                VALUES (%s, %s, %s, %s)
                """,
                [
                    (
                        int(row["ownerID"]),
                        row["oName"],
                        row["residenceCity"],
                        row["bDate"],
                    )
                    for row in owners
                ],
            )

            apartments = list(csv_rows(data_dir / "Apartments.csv"))
            cursor.executemany(
                """
                INSERT INTO Apartments (aID, city, roomsNum, ownerID)
                VALUES (%s, %s, %s, %s)
                """,
                [
                    (
                        int(row["aID"]),
                        row["city"],
                        int(row["roomsNum"]),
                        int(row["ownerID"]),
                    )
                    for row in apartments
                ],
            )

            rentals = list(csv_rows(data_dir / "Rentals.csv"))
            cursor.executemany(
                """
                INSERT INTO Rentals (renterID, rYear, aID, cost)
                VALUES (%s, %s, %s, %s)
                """,
                [
                    (
                        int(row["renterID"]),
                        int(row["rYear"]),
                        int(row["aID"]),
                        int(row["cost"]),
                    )
                    for row in rentals
                ],
            )

            for batch in sql_batches(views_path):
                cursor.execute(batch)

        total = len(owners) + len(apartments) + len(rentals)
        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {total} records and created {len(VIEW_DROP_ORDER)} views."
            )
        )

