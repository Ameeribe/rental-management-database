from datetime import date

from django.db import connection
from django.shortcuts import render


def dict_fetch_all(cursor):
    """Return every row from a cursor as a dictionary."""
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def parse_positive_int(raw_value):
    """Convert user input to a positive integer, or return None."""
    try:
        value = int(str(raw_value).strip())
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def homepage(request):
    return render(request, "home.html")


def queries_page(request):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT F.aID, R.renterID
            FROM few_years_apts AS F
            JOIN rent_ok AS R ON F.aID = R.aID
            WHERE R.cost = (
                SELECT MAX(R2.cost)
                FROM rent_ok AS R2
                WHERE R2.aID = F.aID
            )
            ORDER BY F.aID, R.renterID;
            """
        )
        highest_cost_renters = dict_fetch_all(cursor)

        cursor.execute(
            """
            SELECT DISTINCT A.city
            FROM Rentals AS R
            JOIN Apartments AS A ON R.aID = A.aID
            JOIN sokhir_minimalist AS S ON R.renterID = S.renterID
            JOIN maskir_minimalist AS M ON A.ownerID = M.ownerID
            ORDER BY A.city ASC;
            """
        )
        minimalist_cities = dict_fetch_all(cursor)

        cursor.execute(
            """
            SELECT
                O.oName,
                O.bDate,
                COUNT(DISTINCT A.aID) AS problematic_rented_apartments
            FROM Owners AS O
            JOIN Apartments AS A ON O.ownerID = A.ownerID
            JOIN Rentals AS R ON A.aID = R.aID
            WHERE O.bDate >= '2000-01-01'
              AND R.renterID IN (SELECT renterID FROM ProblematicRenters)
              AND NOT EXISTS (
                  SELECT A2.aID
                  FROM Apartments AS A2
                  WHERE A2.ownerID = O.ownerID
                    AND A2.city = O.residenceCity
              )
              AND (
                  SELECT COUNT(DISTINCT city)
                  FROM Apartments AS A3
                  WHERE A3.ownerID = O.ownerID
              ) = (
                  SELECT COUNT(*)
                  FROM Apartments AS A4
                  WHERE A4.ownerID = O.ownerID
              )
            GROUP BY O.ownerID, O.oName, O.bDate
            ORDER BY O.bDate DESC, O.ownerID ASC;
            """
        )
        owner_patterns = dict_fetch_all(cursor)

    return render(
        request,
        "queries.html",
        {
            "highest_cost_renters": highest_cost_renters,
            "minimalist_cities": minimalist_cities,
            "owner_patterns": owner_patterns,
        },
    )


def add_rental_page(request):
    message = None
    warning = None
    error = None
    current_year = date.today().year

    with connection.cursor() as cursor:
        cursor.execute("SELECT aID FROM Apartments ORDER BY aID ASC")
        apartment_ids = [row[0] for row in cursor.fetchall()]

    if request.method == "POST":
        renter_id = parse_positive_int(request.POST.get("renterID"))
        cost = parse_positive_int(request.POST.get("cost"))
        apartment_id = parse_positive_int(request.POST.get("aID"))

        if renter_id is None or cost is None or cost < 501:
            error = "Enter a valid renter ID and a monthly cost of at least 501."
        elif apartment_id not in apartment_ids:
            error = "Select a valid apartment."
        else:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM Rentals WHERE renterID = %s AND rYear = %s",
                    [renter_id, current_year],
                )
                if cursor.fetchone():
                    error = "A rental agreement already exists for this renter and year."
                else:
                    cursor.execute(
                        "SELECT 1 FROM Rentals WHERE renterID = %s",
                        [renter_id],
                    )
                    if not cursor.fetchone():
                        error = "Renter ID was not found in the historical rental data."
                    else:
                        cursor.execute(
                            """
                            INSERT INTO Rentals (renterID, cost, aID, rYear)
                            VALUES (%s, %s, %s, %s)
                            """,
                            [renter_id, cost, apartment_id, current_year],
                        )
                        message = "Rental added successfully."

                        cursor.execute(
                            """
                            SELECT COUNT(*)
                            FROM Rentals
                            WHERE aID = %s AND rYear = %s
                            """,
                            [apartment_id, current_year],
                        )
                        if cursor.fetchone()[0] > 5:
                            warning = (
                                "This apartment now has more than five renters "
                                "in the same year."
                            )

    return render(
        request,
        "add_rental.html",
        {
            "message": message,
            "warning": warning,
            "error": error,
            "apartments": apartment_ids,
        },
    )


def analytics_page(request):
    search_warning = None
    search_results = None
    stats_result = None
    stats_warning = None

    if request.method == "POST":
        owner_name = request.POST.get("oName", "").strip()
        owner_id_input = request.POST.get("ownerID", "").strip()

        if owner_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT ownerID, oName
                    FROM Owners
                    WHERE LOWER(oName) LIKE LOWER(%s)
                    ORDER BY oName ASC;
                    """,
                    [f"{owner_name}%"],
                )
                search_results = [
                    {"ownerID": row[0], "oName": row[1]} for row in cursor.fetchall()
                ]
            if not search_results:
                search_warning = "No owner matched that name."

        elif owner_id_input:
            owner_id = parse_positive_int(owner_id_input)
            if owner_id is None:
                stats_warning = "Enter a valid positive owner ID."
            else:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT oName FROM Owners WHERE ownerID = %s", [owner_id]
                    )
                    owner_row = cursor.fetchone()

                    if not owner_row:
                        stats_warning = "No owner matched that ID."
                    else:
                        cursor.execute(
                            "SELECT COUNT(*) FROM Apartments WHERE ownerID = %s",
                            [owner_id],
                        )
                        apartment_count = cursor.fetchone()[0]

                        cursor.execute(
                            """
                            SELECT AVG(CAST(renter_count AS FLOAT))
                            FROM (
                                SELECT COUNT(R.renterID) AS renter_count
                                FROM Rentals AS R
                                JOIN Apartments AS A ON R.aID = A.aID
                                WHERE A.ownerID = %s
                                GROUP BY A.aID, R.rYear
                            ) AS owner_rental_counts;
                            """,
                            [owner_id],
                        )
                        average_renters = cursor.fetchone()[0]

                        cursor.execute(
                            """
                            SELECT COUNT(DISTINCT O.ownerID)
                            FROM Owners AS O
                            WHERE O.residenceCity = (
                                SELECT residenceCity
                                FROM Owners
                                WHERE ownerID = %s
                            )
                              AND O.ownerID <> %s;
                            """,
                            [owner_id, owner_id],
                        )
                        nearby_owner_count = cursor.fetchone()[0]

                        stats_result = {
                            "ownerID": owner_id,
                            "ownerName": owner_row[0],
                            "apartmentsCount": apartment_count,
                            "avgRenters": (
                                round(average_renters, 2)
                                if average_renters is not None
                                else "N/A"
                            ),
                            "otherOwnersCount": nearby_owner_count,
                        }
        else:
            search_warning = "Enter an owner name."
            stats_warning = "Enter an owner ID."

    return render(
        request,
        "analytics.html",
        {
            "search_warning": search_warning,
            "search_results": search_results,
            "stats_result": stats_result,
            "stats_warning": stats_warning,
        },
    )

