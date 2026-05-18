CREATE TABLE stations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    location_lat DOUBLE PRECISION,
    location_lon DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE animals (
    id SERIAL PRIMARY KEY,
    tag_id TEXT UNIQUE,
    species TEXT,
    status TEXT,
    station_id INTEGER REFERENCES stations(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    animal_id INTEGER REFERENCES animals(id),
    station_id INTEGER REFERENCES stations(id),
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- vorbereitet für späteres PostGIS Upgrade:
-- ALTER TABLE stations ADD COLUMN geom GEOGRAPHY(Point, 4326);