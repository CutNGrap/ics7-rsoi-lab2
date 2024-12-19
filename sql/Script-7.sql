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


GRANT ALL PRIVILEGES ON table cars TO program;


CREATE TABLE payment
(
    id          SERIAL PRIMARY KEY,
    payment_uid uuid        NOT NULL,
    status      VARCHAR(20) NOT NULL
        CHECK (status IN ('PAID', 'CANCELED')),
    price       INT         NOT NULL
);

GRANT ALL PRIVILEGES ON table payment TO program;



CREATE TABLE rental
(
    id          SERIAL PRIMARY KEY,
    rental_uid  uuid UNIQUE              NOT NULL,
    username    VARCHAR(80)              NOT NULL,
    payment_uid uuid                     NOT NULL,
    car_uid     uuid                     NOT NULL,
    date_from   TIMESTAMP WITH TIME ZONE NOT NULL,
    date_to     TIMESTAMP WITH TIME ZONE NOT NULL,
    status      VARCHAR(20)              NOT NULL
        CHECK (status IN ('IN_PROGRESS', 'FINISHED', 'CANCELED'))
);

GRANT ALL PRIVILEGES ON table rental TO program;
GRANT ALL PRIVILEGES ON table rental_id_seq TO program;
