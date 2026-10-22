-- Smartlytics v2 schema (Supabase Postgres). NOT used by the v1 demo, which keeps
-- everything in session memory. Apply only when accounts are added.
-- Access control: row level security on every table, owner = auth.uid().

create extension if not exists pgcrypto;

-- updated_at trigger
create or replace function set_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;

create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  plan text not null default 'free' check (plan in ('free','pro')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table datasets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id) on delete cascade,
  name text not null,
  storage_path text not null,               -- {user_id}/{dataset_id}/raw.ext in Supabase Storage
  file_kind text not null check (file_kind in ('csv','xlsx')),
  row_count integer not null check (row_count >= 0),
  column_count integer not null check (column_count >= 0),
  status text not null default 'raw' check (status in ('raw','cleaned')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index on datasets (user_id, created_at desc);

create table dataset_columns (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null references datasets(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  position integer not null,
  name text not null,
  dtype text not null check (dtype in ('numeric','category','date')),
  missing_count integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (dataset_id, position)
);
create index on dataset_columns (user_id);

create table audit_entries (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null references datasets(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  step text not null,
  message text not null,
  rows_before integer,
  rows_after integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index on audit_entries (dataset_id, created_at);
create index on audit_entries (user_id);

create table sales_mappings (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null unique references datasets(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  revenue_col text not null,
  cost_col text,
  quantity_col text,
  cost_is_per_unit boolean not null default true,
  date_col text,
  customer_col text,
  product_col text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index on sales_mappings (user_id);

create table tier_results (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null references datasets(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  q25 numeric not null, q75 numeric not null,
  mean_profit numeric not null, min_profit numeric not null, max_profit numeric not null,
  row_count integer not null,
  high_count integer not null, medium_count integer not null, low_count integer not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint q_order check (q25 <= q75)
);
create index on tier_results (dataset_id, created_at desc);
create index on tier_results (user_id);

create table reports (
  id uuid primary key default gen_random_uuid(),
  dataset_id uuid not null references datasets(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  title text not null,
  storage_path text,                        -- rendered HTML in Storage, null until generated
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index on reports (dataset_id);
create index on reports (user_id, created_at desc);

create table saved_charts (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references reports(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  position integer not null,
  title text not null,
  kind text not null check (kind in ('histogram','bar','pie','scatter','correlation','trend','profit_thresholds','sales_vs_profit')),
  params jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (report_id, position)
);
create index on saved_charts (user_id);

-- triggers + RLS for every table
do $$
declare t text;
begin
  foreach t in array array['profiles','datasets','dataset_columns','audit_entries','sales_mappings','tier_results','reports','saved_charts']
  loop
    execute format('create trigger %I_updated before update on %I for each row execute function set_updated_at()', t, t);
    execute format('alter table %I enable row level security', t);
  end loop;
end $$;

create policy own_profile on profiles for all using (id = auth.uid()) with check (id = auth.uid());
do $$
declare t text;
begin
  foreach t in array array['datasets','dataset_columns','audit_entries','sales_mappings','tier_results','reports','saved_charts']
  loop
    execute format('create policy own_rows on %I for all using (user_id = auth.uid()) with check (user_id = auth.uid())', t);
  end loop;
end $$;
