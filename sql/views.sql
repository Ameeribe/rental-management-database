-- Rental agreements whose owner was at least 18 at the start of the rental year.
CREATE OR ALTER VIEW rent_ok AS
SELECT R.*
FROM Rentals AS R
JOIN Apartments AS A ON R.aID = A.aID
JOIN Owners AS O ON A.ownerID = O.ownerID
WHERE DATEADD(YEAR, 18, O.bDate) <= DATEFROMPARTS(R.rYear, 1, 1);
GO

-- Owners for whom no apartment has an ineligible rental agreement.
CREATE OR ALTER VIEW good_owners AS
SELECT O.ownerID
FROM Owners AS O
WHERE NOT EXISTS (
    SELECT 1
    FROM Apartments AS A
    JOIN Rentals AS R ON A.aID = R.aID
    WHERE A.ownerID = O.ownerID
      AND NOT EXISTS (
          SELECT 1
          FROM rent_ok AS RK
          WHERE RK.aID = R.aID
            AND RK.renterID = R.renterID
            AND RK.rYear = R.rYear
      )
);
GO

-- Eligible-owner apartments rented in at most three distinct years.
CREATE OR ALTER VIEW few_years_apts AS
SELECT A.aID
FROM Apartments AS A
JOIN good_owners AS G ON A.ownerID = G.ownerID
LEFT JOIN Rentals AS R ON A.aID = R.aID
GROUP BY A.aID
HAVING COUNT(DISTINCT R.rYear) <= 3;
GO

-- Renters who never paid more than 2,000 and never lived alone in an apartment-year.
CREATE OR ALTER VIEW sokhir_minimalist AS
SELECT R1.renterID
FROM Rentals AS R1
GROUP BY R1.renterID
HAVING MAX(R1.cost) <= 2000
   AND NOT EXISTS (
       SELECT 1
       FROM Rentals AS R2
       WHERE R2.renterID = R1.renterID
         AND NOT EXISTS (
             SELECT 1
             FROM Rentals AS R3
             WHERE R3.aID = R2.aID
               AND R3.rYear = R2.rYear
               AND R3.renterID <> R2.renterID
         )
   );
GO

-- Owners whose rented apartment-year combinations never exceed three renters.
CREATE OR ALTER VIEW maskir_minimalist AS
SELECT O.ownerID
FROM Owners AS O
WHERE NOT EXISTS (
    SELECT 1
    FROM Apartments AS A
    JOIN Rentals AS R ON A.aID = R.aID
    WHERE A.ownerID = O.ownerID
    GROUP BY A.aID, R.rYear
    HAVING COUNT(DISTINCT R.renterID) > 3
);
GO

-- Unique renter pairs that shared an apartment during the same year.
CREATE OR ALTER VIEW Roommates AS
SELECT
    R1.renterID AS renter1,
    R2.renterID AS renter2,
    R1.aID,
    R1.rYear
FROM Rentals AS R1
JOIN Rentals AS R2
  ON R1.aID = R2.aID
 AND R1.rYear = R2.rYear
 AND R1.renterID < R2.renterID;
GO

-- Renter pairs that shared an apartment-year more than once.
CREATE OR ALTER VIEW RepeatedRoommates AS
SELECT renter1, renter2
FROM Roommates
GROUP BY renter1, renter2
HAVING COUNT(*) > 1;
GO

-- Renters who do not appear in a repeated roommate pair.
CREATE OR ALTER VIEW ProblematicRenters AS
SELECT DISTINCT R.renterID
FROM Rentals AS R
LEFT JOIN RepeatedRoommates AS RR1 ON R.renterID = RR1.renter1
LEFT JOIN RepeatedRoommates AS RR2 ON R.renterID = RR2.renter2
WHERE RR1.renter1 IS NULL
  AND RR2.renter2 IS NULL;
GO

