-- file: 10-create-user.sql
CREATE ROLE program WITH PASSWORD 'test';

ALTER ROLE program WITH LOGIN;

CREATE DATABASE cars;
GRANT ALL PRIVILEGES ON DATABASE cars TO program;

CREATE DATABASE rentals;
GRANT ALL PRIVILEGES ON DATABASE rentals TO program;

CREATE DATABASE payments;
GRANT ALL PRIVILEGES ON DATABASE payments TO program;


INSERT INTO cars (car_uid, brand, model, registration_number, power, price, type, availability)
VALUES (
    '109b42f3-198d-4c89-9276-a7520a7120ab', 
    'Mercedes Benz', 
    'GLA 250', 
    'ЛО777Х799', 
    249, 
    3500, 
    'SEDAN', 
    TRUE
);


CREATE TABLE cars
(
    id                  SERIAL PRIMARY KEY,
    car_uid             uuid UNIQUE NOT NULL,
    brand               VARCHAR(80) NOT NULL,
    model               VARCHAR(80) NOT NULL,
    registration_number VARCHAR(20) NOT NULL,
    power               INT,
    price               INT         NOT NULL,
    type                VARCHAR(20)
        CHECK (type IN ('SEDAN', 'SUV', 'MINIVAN', 'ROADSTER')),
    availability        BOOLEAN     NOT NULL
);