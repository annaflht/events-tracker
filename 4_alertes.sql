-- Table des inscrits aux alertes (créée le 25/11/2026)
create table if not exists public.subscribers (
  id bigint generated always as identity primary key,
  email text not null unique check (email ~* '^[^\s@]+@[^\s@]+\.[^\s@]{2,}$' and length(email) <= 254),
  wants_spring boolean not null default true,
  wants_events boolean not null default true,
  zones text[] not null default '{}' check (cardinality(zones) <= 10),
  confirmed boolean not null default false,
  created_at timestamptz not null default now()
);
alter table public.subscribers enable row level security;
-- Le site peut seulement ajouter une adresse : aucune règle de lecture, donc personne ne peut lire la liste avec la clé publique.
create policy "inscription publique" on public.subscribers for insert to anon, authenticated with check (confirmed = false);
grant insert (email, wants_spring, wants_events, zones) on public.subscribers to anon, authenticated;
