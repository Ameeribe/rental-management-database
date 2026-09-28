"""Read-only mappings for tables with single-column primary keys.

The Rentals table uses a composite primary key (renterID, rYear), so this
project accesses it with parameterized SQL rather than an inaccurate Django
model mapping.
"""

from django.db import models


class Owner(models.Model):
    owner_id = models.IntegerField(db_column="ownerID", primary_key=True)
    name = models.CharField(db_column="oName", max_length=50)
    residence_city = models.CharField(db_column="residenceCity", max_length=50)
    birth_date = models.DateField(db_column="bDate")

    class Meta:
        managed = False
        db_table = "Owners"

    def __str__(self):
        return f"{self.name} ({self.owner_id})"


class Apartment(models.Model):
    apartment_id = models.IntegerField(db_column="aID", primary_key=True)
    city = models.CharField(max_length=50)
    room_count = models.IntegerField(db_column="roomsNum")
    owner = models.ForeignKey(
        Owner,
        models.DO_NOTHING,
        db_column="ownerID",
        related_name="apartments",
    )

    class Meta:
        managed = False
        db_table = "Apartments"

    def __str__(self):
        return f"Apartment {self.apartment_id} - {self.city}"

