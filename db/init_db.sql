
SELECT * FROM pg_extension;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


CREATE TABLE IF NOT EXISTS problems (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  "text" varchar(1000) NOT NULL,
  label varchar(255) NOT NULL,
  PRIMARY KEY (id)
);