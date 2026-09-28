CREATE TABLE Owners (
    ownerID INT PRIMARY KEY,
    oName VARCHAR(50) NOT NULL,
    residenceCity VARCHAR(50) NOT NULL,
    bDate DATE NOT NULL
);
GO

CREATE TABLE Apartments (
    aID INT PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    roomsNum INT NOT NULL CHECK (roomsNum > 0),
    ownerID INT NOT NULL,
    CONSTRAINT FK_Apartments_Owners
        FOREIGN KEY (ownerID) REFERENCES Owners(ownerID)
);
GO

CREATE TABLE Rentals (
    renterID INT NOT NULL,
    rYear INT NOT NULL,
    aID INT NOT NULL,
    cost INT NOT NULL CHECK (cost > 0),
    CONSTRAINT PK_Rentals PRIMARY KEY (renterID, rYear),
    CONSTRAINT FK_Rentals_Apartments
        FOREIGN KEY (aID) REFERENCES Apartments(aID)
);
GO

