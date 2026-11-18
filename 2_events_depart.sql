-- ============================================================
-- 2_events_depart.sql — à coller UNE SEULE FOIS, après 1_tables.sql
-- Ajoute les 12 events déjà repérés (vérifiés le 18/11/2026).
-- ============================================================
insert into public.events
  (id, firm, title, type, cat, zone, city, event_start, event_label, opens, deadline, rolling, elig, prev, url, link_label, source)
values
('https://www.groupebpce.com/toute-l-actualite/natixis-investment-managers-lancement-de-the-students-challenge-3/',
 'Natixis IM (Groupe BPCE)', 'The Students Challenge (7e édition)', 'Compétition', 'Asset Mgmt', 'France', 'Paris',
 null, 'Non précisée', '2026-11-03', '2026-11-25', false,
 'Fin de cycle ou master (écoles de commerce, d''ingénieurs, universités). Équipes de 5 ou 6.', null,
 'https://www.groupebpce.com/toute-l-actualite/natixis-investment-managers-lancement-de-the-students-challenge-3/', 'Voir l''annonce', 'manuel'),

('https://jobs.smartrecruiters.com/ni/Wiser/70283804-8a3b-4744-b7ee-e0e5df870e17-evercore-women-in-finance-event-paris-office',
 'Evercore', 'Women in Finance Event – Paris Office', 'Women in Finance', 'Elite Boutique', 'France', 'Paris',
 '2026-10-15', null, null, '2026-10-15', false,
 'Étudiantes diplômées en 2027 ou 2028, tous cursus.', 'Prochaine édition attendue à l''automne 2027',
 'https://jobs.smartrecruiters.com/ni/Wiser/70283804-8a3b-4744-b7ee-e0e5df870e17-evercore-women-in-finance-event-paris-office', 'Page de l''event', 'manuel'),

('talnet:rothschildandco.tal.net:1050',
 'Rothschild & Co', 'Discover Rothschild & Co Insight Day', 'Insight Day', 'Elite Boutique', 'Royaume-Uni', 'Londres',
 '2026-12-15', null, null, null, true,
 'Étudiants visant le Summer ou le Long-Term Internship UK. Sur invitation, CV demandé.', null,
 'https://rothschildandco.tal.net/vx/lang-en-GB/mobile-0/appcentre-1/brand-4/candidate/so/pm/1/pl/1/opp/1050-2026-Discover-Rothschild-Co-Insight-Day/en-GB', 'S''inscrire', 'manuel'),

('https://www.citadelsecurities.com/careers/students/discover-citadel-securities/emea-apply/',
 'Citadel & Citadel Securities', 'Discover Citadel – EMEA (2 jours)', 'Insight Day', 'Trading & Quant', 'Royaume-Uni', 'Londres',
 '2027-03-25', 'Fin mars 2027', null, '2027-01-29', false,
 '1re ou 2e année, diplôme entre déc. 2028 et juin 2030, résidant en Europe. Réponse le 5 février 2027.', null,
 'https://www.citadelsecurities.com/careers/students/discover-citadel-securities/emea-apply/', 'S''inscrire', 'manuel'),

('https://www.citadelsecurities.com/careers/programs-and-events/citadel-securities-spark/apply-london/',
 'Citadel Securities', 'Citadel Securities Spark – London', 'Insight Day', 'Trading & Quant', 'Royaume-Uni', 'Londres',
 '2027-03-30', '30 mars – 1er avril 2027', null, '2027-02-19', false,
 'Éligibilité à vérifier sur la page d''inscription.', null,
 'https://www.citadelsecurities.com/careers/programs-and-events/citadel-securities-spark/apply-london/', 'S''inscrire', 'manuel'),

('https://www.janestreet.com/apply-insight-ldn/',
 'Jane Street', 'INSIGHT London', 'Women in Finance', 'Trading & Quant', 'Royaume-Uni', 'Londres',
 '2027-04-05', '5 – 10 avril 2027', null, '2027-01-03', false,
 'Femmes, personnes trans ou non-binaires inscrites dans une université EMEA. Deadline relevée sur des sites tiers.', null,
 'https://www.janestreet.com/apply-insight-ldn/', 'S''inscrire', 'manuel'),

('https://www.rbccm.com/en/careers/programs',
 'RBC Capital Markets', 'Spring Insight Programmes 2027 (2 jours)', 'Insight Day', 'Banque d''investissement', 'Royaume-Uni', 'Londres',
 null, 'Printemps 2027', '2026-12-01', null, false,
 'En 2025 : 1re année d''un cursus en 3 ans. Ouverture annoncée en décembre 2026.', 'Édition 2025 à Londres',
 'https://www.rbccm.com/en/careers/programs', 'Page programmes', 'manuel'),

('https://www.evercore.com/careers/students-graduates/students-graduates-europe-asia/#wif-london',
 'Evercore', 'Women in Finance Campus Recruiting Event', 'Women in Finance', 'Elite Boutique', 'Royaume-Uni', 'Londres',
 '2026-09-08', null, null, '2026-08-19', false,
 'Étudiantes, tous cursus. Panel puis networking.', 'Prochaine édition attendue en septembre 2027',
 'https://www.evercore.com/careers/students-graduates/students-graduates-europe-asia/', 'Page étudiants', 'manuel'),

('https://morganstanley.tal.net/#women-who-lead-2026',
 'Morgan Stanley', 'Women Who Lead (Institutional Equities, Quantitative Finance)', 'Women in Finance', 'Bulge Bracket', 'Royaume-Uni', 'Londres',
 '2026-09-30', null, null, '2026-09-30', false,
 'Étudiantes.', 'Prochaine édition attendue en septembre 2027',
 'https://morganstanley.tal.net/vx/lang-en-GB/mobile-0/brand-2/xf-69c3955e6630/candidate/jobboard/vacancy/2/adv/', 'Campus Events', 'manuel'),

('https://lazard.com/careers/events/women-in-banking-breakfast-london-financial-advisory',
 'Lazard', 'Women in Banking Breakfast', 'Women in Finance', 'Elite Boutique', 'Royaume-Uni', 'Londres',
 '2025-10-15', null, null, '2025-10-15', false,
 'Étudiantes. Petit-déjeuner au bureau de Londres.', 'Attendu en sept.-oct. 2027',
 'https://lazard.com/careers/events/women-in-banking-breakfast-london-financial-advisory', 'Page de l''event', 'manuel'),

('talnet:morganstanley.tal.net:22388',
 'Morgan Stanley', '2027 Spring Insight : Finance, Risk & Business Services', 'Insight Day', 'Bulge Bracket', 'Royaume-Uni', 'Glasgow',
 '2027-04-07', null, null, '2027-03-21', true,
 '1re et 2e année. 15h-17h au bureau de Glasgow.', null,
 'https://morganstanley.tal.net/vx/lang-en-GB/mobile-0/brand-2/candidate/so/pm/1/pl/2/opp/22388-2027-Spring-Insight-Careers-Across-Finance-Risk-Business-Services-Glasgow/en-GB', 'S''inscrire', 'manuel'),

('talnet:morganstanley.tal.net:22453',
 'Morgan Stanley', '2027 Technology Spring Insight', 'Insight Day', 'Bulge Bracket', 'Royaume-Uni', 'Glasgow',
 '2027-04-08', null, null, null, false,
 'Orienté tech. Détails donnés avec l''invitation.', null,
 'https://morganstanley.tal.net/vx/lang-en-GB/mobile-0/brand-2/candidate/so/pm/1/pl/2/opp/22453-2027-Technology-Spring-Insight-Glasgow/en-GB', 'S''inscrire', 'manuel')
on conflict (id) do nothing;
