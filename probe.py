import requests, re, json, time
UA={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36","Accept-Language":"en-GB,en;q=0.9"}
T=[
 ("hsbc-search","https://mycareer.hsbc.com/en_GB/external/SearchJobs/?search=intern&jobRecordsPerPage=50"),
 ("hsbc-feed","https://mycareer.hsbc.com/en_GB/external/SearchJobs/feed/?search=intern"),
 ("amundi-rss","https://jobs.amundi.com/handlers/offerRss.ashx?LCID=2057"),
 ("amundi-list","https://jobs.amundi.com/job/list-of-jobs.aspx?LCID=2057"),
 ("amundi-list-fr","https://jobs.amundi.com/offre-de-emploi/liste-offres.aspx"),
 ("ca-rss","https://groupecreditagricole.jobs/handlers/offerRss.ashx?LCID=1036"),
 ("ca-list","https://groupecreditagricole.jobs/fr/nos-offres/"),
 ("bnp","https://group.bnpparibas/en/careers/all-job-offers?q=intern"),
 ("nordea-rss","https://careers.nordea.com/services/rss/job/?locale=en_GB&keywords=student"),
 ("nordea-search","https://careers.nordea.com/search/?q=student&sortColumn=referencedate&sortDirection=desc"),
 ("ey-rss","https://careers.ey.com/services/rss/job/?locale=en_US&keywords=intern"),
 ("abg-rss","https://abgsc.teamtailor.com/jobs.rss"),
 ("pareto-rss","https://paretosecurities.teamtailor.com/jobs.rss"),
 ("seb-lever","https://api.eu.lever.co/v0/postings/seb?mode=json"),
 ("gs-sitemap","https://higher.gs.com/sitemap.xml"),
 ("gs-results","https://higher.gs.com/results?EXPERIENCE_LEVEL=Students&page=1&sort=POSTED_DATE"),
 ("moodys-jibe","https://careers.moodys.com/api/jobs?keywords=intern&limit=10"),
 ("muse","https://www.themuse.com/api/public/jobs?level=Internship&category=Accounting%20and%20Finance&page=0"),
 ("danske","https://danskebank.com/careers/search-jobs"),
 ("natixis","https://www.natixis.com/en/careers/job-offers"),
 ("sg-api","https://careers.societegenerale.com/en/search?query=intern"),
 ("axa","https://careers.axa.com/careers-home/jobs?keywords=intern"),
 ("allianz","https://careers.allianz.com/en_US/jobs.html"),
 ("jobteaser-robots","https://www.jobteaser.com/robots.txt"),
 ("wttj-robots","https://www.welcometothejungle.com/robots.txt"),
]
for name,u in T:
    try:
        r=requests.get(u,headers=UA,timeout=25)
        b=r.text
        print(f"=== {name} {r.status_code} {r.headers.get('content-type','')} len={len(b)}")
        if name.endswith("robots"): print(b[:1500]); continue
        titles=re.findall(r"<title>(.*?)</title>",b,re.S)[:6]
        print(" titles:",[t.strip()[:90] for t in titles])
        links=set(re.findall(r'href="([^"]*(?:JobDetail|/job/|/offre|jobs/\d|PipelineDetail|/roles/)[^"]*)"',b))
        print(" joblinks:",len(links),list(links)[:4])
        if "json" in r.headers.get('content-type',''): print(" json:",b[:600])
        else: print(" snippet:",re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",b))[:400])
    except Exception as e: print("===",name,"ERR",e)
    time.sleep(1)
