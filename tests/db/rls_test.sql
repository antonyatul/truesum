-- Row-level security test for replica/schema.sql against plain Postgres.
-- Stubs the two Supabase pieces the schema relies on (auth.users, auth.uid())
-- and the 'authenticated' role, then proves user B can't see or touch user A's rows.
-- Run: psql -v ON_ERROR_STOP=1 -f tests/db/supabase_stub.sql -f replica/schema.sql -f tests/db/rls_test.sql

\set a '00000000-0000-0000-0000-00000000000a'
\set b '00000000-0000-0000-0000-00000000000b'

-- seed as superuser (bypasses RLS)
insert into auth.users (id) values (:'a'), (:'b');
insert into profiles (id, display_name) values (:'a', 'User A'), (:'b', 'User B');
insert into datasets (id, user_id, name, storage_path, file_kind, row_count, column_count)
values ('10000000-0000-0000-0000-000000000001', :'a', 'a.csv', 'a/1/raw.csv', 'csv', 10, 3);
insert into reports (id, dataset_id, user_id, title)
values ('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', :'a', 'A report');

grant usage on schema public to authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;

-- ---- act as user B -------------------------------------------------------
set role authenticated;
select set_config('request.jwt.claim.sub', :'b', false);

do $$
declare n int;
begin
  select count(*) into n from datasets;      if n <> 0 then raise exception 'B can read A''s datasets (%)', n; end if;
  select count(*) into n from reports;       if n <> 0 then raise exception 'B can read A''s reports (%)', n; end if;
  select count(*) into n from profiles;      if n <> 1 then raise exception 'B should see only own profile, saw %', n; end if;

  update datasets set name = 'hacked';       get diagnostics n = row_count;
  if n <> 0 then raise exception 'B updated A''s dataset'; end if;
  delete from datasets;                      get diagnostics n = row_count;
  if n <> 0 then raise exception 'B deleted A''s dataset'; end if;

  begin
    insert into datasets (user_id, name, storage_path, file_kind, row_count, column_count)
    values ('00000000-0000-0000-0000-00000000000a', 'forged.csv', 'x', 'csv', 1, 1);
    raise exception 'B inserted a row owned by A';
  exception when insufficient_privilege then null;  -- expected: RLS with check
  end;

  insert into datasets (user_id, name, storage_path, file_kind, row_count, column_count)
  values ('00000000-0000-0000-0000-00000000000b', 'b.csv', 'b/1/raw.csv', 'csv', 5, 2);
  select count(*) into n from datasets;      if n <> 1 then raise exception 'B should see own dataset, saw %', n; end if;
end $$;

-- ---- act as user A -------------------------------------------------------
select set_config('request.jwt.claim.sub', :'a', false);
do $$
declare n int; nm text;
begin
  select count(*), max(name) into n, nm from datasets;
  if n <> 1 or nm <> 'a.csv' then raise exception 'A should see exactly own untouched dataset, saw % (%)', n, nm; end if;
end $$;

-- ---- constraints and cascade (as superuser) --------------------------------
reset role;
do $$
begin
  begin
    insert into datasets (user_id, name, storage_path, file_kind, row_count, column_count)
    values ('00000000-0000-0000-0000-00000000000a', 'bad', 'x', 'pdf', 1, 1);
    raise exception 'file_kind check did not fire';
  exception when check_violation then null;
  end;
  begin
    insert into tier_results (dataset_id, user_id, q25, q75, mean_profit, min_profit, max_profit, row_count, high_count, medium_count, low_count)
    values ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-00000000000a', 5, 1, 0, 0, 0, 1, 0, 0, 0);
    raise exception 'q25 <= q75 check did not fire';
  exception when check_violation then null;
  end;
end $$;

delete from auth.users where id = :'a';   -- account deletion must remove everything they own
do $$
declare n int;
begin
  select count(*) into n from datasets where user_id = '00000000-0000-0000-0000-00000000000a';
  if n <> 0 then raise exception 'account deletion left % datasets behind', n; end if;
  select count(*) into n from reports;
  if n <> 0 then raise exception 'account deletion left % reports behind', n; end if;
end $$;

select 'RLS TEST PASSED' as result;
