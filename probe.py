import requests, re, json, time
UA={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36","Accept-Language":"en-GB,en;q=0.9"}
def get(u,**k):
    try: return requests.get(u,headers={**UA,**k.pop('h',{})},timeout=25,**k)
    except Exception as e: print("  ERR",u,e); return None
print("##### HSBC")
r=get("https://mycareer.hsbc.com/en_GB/external/SearchJobs/?search=intern&jobRecordsPerPage=50")
if r is not None:
    b=r.text
    for m in re.finditer(r"(?i)(jobdetail|pipelinedetail|ajax|json|api/|searchjobs[a-z]*)",b):
        pass
    print(sorted(set(re.findall(r'(?:src|href|action)="([^"]+)"',b)))[:60])
    print(sorted(set(re.findall(r'["\'](/[^"\' ]*(?:Search|Job|ajax|Data)[^"\' ]*)["\']',b)))[:40])
for u in ["https://mycareer.hsbc.com/en_GB/external/SearchJobs/feed/","https://mycareer.hsbc.com/en_GB/external/SearchJobs/feed/?jobRecordsPerPage=100",
          "https://mycareer.hsbc.com/en_GB/external/SearchJobs/?listFilterMode=1&jobRecordsPerPage=100&jobOffset=0&search=intern"]:
    r=get(u); 
    if r is not None: print(u,r.status_code,len(r.text),len(re.findall(r"JobDetail|PipelineDetail",r.text)),re.sub(r"\s+"," ",r.text[:300]))
print("##### Talentsoft guesses")
for h in ["jobs.ca-cib.com","recrutement.bpce.fr","recrutement.natixis.com","careers.natixis.com","emploi.labanquepostale.fr","oddo-bhf.talent-soft.com",
          "edmond-de-rothschild.talent-soft.com","careers.edmond-de-rothschild.com","bpifrance.talent-soft.com","recrutement.bpifrance.fr","cic.talent-soft.com",
          "recrutement.creditmutuel.fr","axa-im.talent-soft.com","careers.lcl.fr","jobs.indosuez.com","careers.ofi-invest.com","ostrum.talent-soft.com","careers.caceis.com",
          "rothschildandco.talent-soft.com","careers.mirova.com","jobs.allianz.fr","recrutement.groupama.fr","carrieres.cnp.fr","careers.scor.com","jobs.lazard.fr","tikehau.talent-soft.com"]:
    r=get(f"https://{h}/handlers/offerRss.ashx")
    if r is not None: print(h,r.status_code,r.headers.get('content-type',''),r.text.count("<item>"))
    time.sleep(0.5)
print("##### SuccessFactors RSS guesses")
for h in ["careers.swissre.com","jobs.zurich.com","careers.danskebank.com","jobs.commerzbank.com","jobs.dzbank.de","karriere.deka.de","careers.kfw.de","jobs.helaba.com",
          "careers.lbbw.de","jobs.standardchartered.com","careers.allianz.com","jobs.allianz.com","careers.munichre.com","careers.generali.com","careers.unicredit.eu",
          "careers.intesasanpaolo.com","jobs.ing.com","careers.abnamro.com","careers.rabobank.com","careers.kbc.com","careers.belfius.be","careers.swedbank.com",
          "careers.handelsbanken.com","careers.dnb.no","jobs.erstegroup.com","careers.raiffeisen.ch","jobs.juliusbaer.com","careers.pictet.com","careers.lombardodier.com",
          "jobs.vontobel.com","careers.efgbank.com","careers.ubp.com","jobs.santander.com","careers.bbva.com","careers.caixabank.com","jobs.nykredit.dk","careers.jyskebank.dk"]:
    r=get(f"https://{h}/services/rss/job/?locale=en_US&keywords=(intern)")
    if r is not None: print(h,r.status_code,r.headers.get('content-type','')[:25],r.text.count("<item>"))
    time.sleep(0.5)
print("##### Teamtailor guesses")
for c in ["carnegie","dnbcarnegie","arcticsecurities","arctic","nordnet","fearnleysecurities","clarksons","danskebank","sparebank1markets","sb1markets","redeye","penser","hagstromer","abgsc","paretosecurities","nordea","handelsbanken","swedbank","catella","eqt","nordic-capital","triton","altor","ik-partners","cinven","permira","ardian","eurazeo","tikehau"]:
    r=get(f"https://{c}.teamtailor.com/jobs.rss")
    if r is not None and r.status_code==200: print(c,r.text.count("<item>"))
    time.sleep(0.3)
print("##### Lever EU guesses")
for c in ["seb","nordnet","klarna","eqt","northzone","creandum","avanza","lunar","qonto","swan","revolut","wise"]:
    r=get(f"https://api.eu.lever.co/v0/postings/{c}?mode=json")
    if r is not None and r.status_code==200:
        js=r.json(); print(c,len(js),[j.get('text') for j in js if re.search(r'(?i)intern|student|trainee|graduate|praktik|stage',j.get('text',''))][:8])
print("##### TalentBrew guesses")
q="search-jobs/results?ActiveFacetID=0&CurrentPage=1&RecordsPerPage=100&Distance=50&RadiusUnitType=0&Keywords=intern&Location=&ShowRadius=False&IsPagination=False&CustomFacetName=&FacetTerm=&FacetType=0&SearchResultsModuleName=Search+Results&SearchFiltersModuleName=Search+Filters&SortCriteria=0&SortDirection=0&SearchType=5"
for b in ["https://careers.moodys.com/en","https://jobs.lloydsbankinggroup.com","https://jobs.natwestgroup.com","https://jobs.natwest.com","https://careers.lseg.com","https://jobs.standardchartered.com",
          "https://careers.statestreet.com","https://jobs.schroders.com","https://careers.mandg.com","https://jobs.aviva.co.uk","https://careers.spglobal.com","https://jobs.santander.co.uk",
          "https://careers.blackrock.com","https://jobs.hsbc.com","https://careers.bnymellon.com","https://jobs.northerntrust.com","https://careers.invesco.com","https://jobs.ubs.com",
          "https://careers.mufgemea.com","https://careers.nomura.com","https://jobs.bnpparibas.com","https://careers.lazard.com","https://jobs.fidelity.com","https://careers.pimco.com",
          "https://careers.morningstar.com","https://careers.fitchratings.com","https://jobs.vanguard.com","https://careers.troweprice.com","https://careers.jpmorgan.com","https://jobs.credit-agricole.com"]:
    r=get(f"{b}/{q}",h={"X-Requested-With":"XMLHttpRequest","Accept":"application/json"})
    if r is None: continue
    try: html=r.json().get("results","")
    except Exception: html=r.text if r.status_code==200 and 'json' in r.headers.get('content-type','') else ""
    t=re.findall(r'<h2[^>]*>(.*?)</h2>',html,re.S)
    print(b,r.status_code,len(re.findall(r'href="[^"]*/job/',html)),[re.sub('<[^>]+>|\\s+',' ',x).strip()[:50] for x in t[:6]])
    time.sleep(0.5)
print("##### Credit Agricole WP")
for u in ["https://groupecreditagricole.jobs/wp-json/","https://groupecreditagricole.jobs/fr/nos-offres/?search=stage"]:
    r=get(u)
    if r is not None:
        b=r.text; print(u,r.status_code,len(b))
        print(sorted(set(re.findall(r'"(/wp-json/[^"]{0,60}|https://groupecreditagricole\.jobs/wp-json/[^"]{0,60})"',b.replace('\\/','/'))))[:40])
        print(sorted(set(re.findall(r'href="([^"]*(?:offre|job)[^"]*)"',b)))[:15])
