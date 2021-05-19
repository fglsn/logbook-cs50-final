create table users
(
	id bigserial primary key,
	email varchar not null unique,
	hash varchar not null,
	created_at timestamptz not null default now()
);

create table vehicles
(	
	id bigserial primary key,
	reg_num varchar not null,
	allowance numeric(10, 2) not null,
	odometer int not null,
	user_id bigint not null references users(id),
	created_at timestamptz not null default now(),
	modified_at timestamptz not null default now()
);

create table sessions
(
	id varchar primary key,
	user_id bigint not null references users(id),
	created_at timestamptz not null default now()
);

create table rides
(
    id bigserial primary key,
    vehicle_id bigint NOT NULL references vehicles(id),
    started_at timestamp with time zone NOT NULL,
    finished_at timestamp with time zone NOT NULL,
    odometer_start integer NOT NULL,
    distance integer NOT NULL,
    allowance numeric(10,2) NOT NULL,
    route varchar,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    modified_at timestamp with time zone NOT NULL DEFAULT now()
);