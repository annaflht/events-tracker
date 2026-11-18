# Events Tracker Finance

Tracker des events étudiants des banques (Women in Finance, insight days, office visits), mis à jour automatiquement.

| Fichier | Rôle |
|---|---|
| `index.html` | le site (lit les events dans Supabase) |
| `robot/run.py` | le robot qui cherche les nouveaux events |
| `robot/sources.json` | la liste des pages surveillées |
| `.github/workflows/robot.yml` | lance le robot toutes les 30 minutes |
| `supabase/1_tables.sql` | crée les tables (à coller une fois dans Supabase) |
| `supabase/2_events_depart.sql` | ajoute les 12 premiers events (à coller une fois) |

Le guide pas à pas explique chaque étape.
