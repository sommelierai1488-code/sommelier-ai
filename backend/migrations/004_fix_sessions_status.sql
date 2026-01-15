-- Migration 004: extend sessions.status to include in_progress

alter table sessions drop constraint if exists sessions_status_check;

alter table sessions
add constraint sessions_status_check
check (status in ('in_progress', 'completed', 'abandoned'));
