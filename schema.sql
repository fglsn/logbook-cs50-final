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