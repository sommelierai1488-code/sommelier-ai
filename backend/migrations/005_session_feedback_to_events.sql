-- Migration 005: rename session_feedback to session_events and allow null action

alter table if exists session_feedback rename to session_events;

-- allow impressions with action null
alter table if exists session_events alter column action drop not null;
