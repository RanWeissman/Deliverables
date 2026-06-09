CREATE DATABASE vehicle_db;
CREATE DATABASE rental_db;

\c rental_db
CREATE EXTENSION IF NOT EXISTS btree_gist;
