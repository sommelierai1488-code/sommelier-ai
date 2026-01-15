-- Migration 006: enforce unique(session_id, sku) on session_events after rename

do $$
begin
    if exists (
        select 1
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where c.relname = 'session_events'
          and n.nspname = 'public'
    ) then
        if not exists (
            select 1
            from pg_constraint con
            join pg_class t on t.oid = con.conrelid
            join pg_namespace n on n.oid = t.relnamespace
            where t.relname = 'session_events'
              and n.nspname = 'public'
              and con.contype in ('u','p')
              and pg_get_constraintdef(con.oid) like '%(session_id, sku)%'
        ) then
            alter table public.session_events
            add constraint session_events_session_sku_unique unique (session_id, sku);
        end if;
    end if;
end;
$$;
