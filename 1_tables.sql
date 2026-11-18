-- ============================================================
-- 1_tables.sql  — à coller UNE SEULE FOIS dans Supabase > SQL Editor
-- Crée les 2 tables du tracker et règle qui peut lire / écrire.
-- ============================================================

-- Table 1 : les events affichés sur le site
create table if not exists public.events (
  id          text primary key,              -- identifiant unique (l'URL de l'event)
  firm        text not null,                 -- banque
  title       text not null,                 -- nom de l'event
  type        text,                          -- Women in Finance, Insight Day, ...
  cat         text,                          -- Bulge Bracket, Elite Boutique, ...
  zone        text,                          -- France, Royaume-Uni, Europe, Virtuel, ...
  city        text,
  event_start date,                          -- date de l'event (si connue)
  event_label text,                          -- date écrite en toutes lettres si floue ("Fin mars 2027")
  opens       date,                          -- ouverture des candidatures (si connue)
  deadline    date,                          -- date limite (si connue)
  rolling     boolean default false,         -- candidatures étudiées au fil de l'eau
  elig        text,                          -- pour qui
  prev        text,                          -- édition précédente
  url         text not null,                 -- lien d'inscription
  link_label  text default 'S''inscrire',
  source      text,                          -- quel robot l'a trouvé ("manuel" si ajouté à la main)
  first_seen  timestamptz default now(),     -- date de détection
  active      boolean default true           -- false = masqué du site
);

-- Table 2 : l'état de chaque source surveillée (pour détecter une page qui change ou un robot cassé)
create table if not exists public.source_state (
  source_id   text primary key,
  last_hash   text,
  fail_count  int default 0,
  last_ok     timestamptz
);

-- Sécurité : on active la protection (Row Level Security) sur les 2 tables
alter table public.events       enable row level security;
alter table public.source_state enable row level security;

-- Tout le monde (le site) peut LIRE les events actifs. Personne ne peut écrire avec la clé publique.
drop policy if exists "lecture publique des events" on public.events;
create policy "lecture publique des events" on public.events
  for select to anon, authenticated using (active = true);

-- Droits : lecture pour le site, tout pour le robot (clé secrète)
grant select on public.events to anon, authenticated;
grant all on public.events, public.source_state to service_role;
-- source_state n'a aucune policy : invisible pour le site, seul le robot y accède.
