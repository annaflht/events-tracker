import requests, re, json, time, concurrent.futures as cf
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36","Accept":"application/json"}
STU=re.compile(r"intern|graduate|analyst program|spring|insight|summer|off[- ]?cycle|placement|new grad|campus|student|trainee|stage|stagiaire",re.I)
names="""ardian eqt eqtgroup kkr carlyle apollo baincapital warburgpincus generalatlantic tpg adventinternational cinven permira hgcapital bridgepoint paigroup eurazeo tikehaucapital antin antinip partnersgroup brookfield oaktree oaktreecapital aresmanagement ares hpsinvestmentpartners bluecrest brevanhoward capula capulainvestment rokos rokoscapital exoduspoint lmrpartners verition eislercapital balyasny bamfunds millennium twosigma deshaw hudsonrivertrading sig susquehanna towerresearch gresearch squarepoint mangroup aqrcapital bridgewater pimco wellington wellingtonmanagement schroders jupiter ninetyone abrdn lgim nomura mizuho natixis lazard pjtpartners centerview moelis evercore perellaweinberg guggenheim greenhill houlihanlokey harriswilliams rwbaird raymondjames stifel jefferies tdcowen rothschild macquarie rbc bmo scotiabank cibc natwest lloyds santander bbva unicredit mediobanca keplercheuvreux oddobhf alantra degroofpetercam pictet lombardodier juliusbaer vontobel efginternational ubs bnpparibas societegenerale creditagricole cacib lazardfreres numis peelhunt panmureliberum cavendish investec evelyn rathbones brewin quilter hargreaveslansdown ajbell wise revolut monzo klarna adyen stripe citadel citadelsecurities janestreet optiver imc flowtraders da-vinci davinci davincitrading mako makogroup maven tibra tibracapital akunacapital fiverings ctc chicagotradingcompany drw jumptrading peak6 belvedere wolverine wolverinetrading jaxtrading headlands xtxmarkets qrt quadrature qubert gsacapital marshallwace lansdowne lansdownepartners egerton odey ruffer sloanerobinson trium vitol trafigura glencore gunvor mercuria bpcredit ingrid arrowgrass hiscox lloydsbankinggroup barclays hsbc standardchartered deutschebank commerzbank dzbank lbbw helaba bayernlb abnamro ing rabobank nordea seb danskebank handelsbanken kbc belfius bnymellon statestreet northerntrust fidelity vanguard invesco troweprice nuveen""".split()
def g(url,**k):
    try: return requests.get(url,headers=UA,timeout=20,**k)
    except Exception as e: return None
def gh(n):
    r=g(f"https://boards-api.greenhouse.io/v1/boards/{n}/jobs")
    if r and r.status_code==200:
        js=r.json().get("jobs",[]); s=[j["title"] for j in js if STU.search(j["title"])]
        if js: return f"GH {n} {len(js)} | stu {len(s)} | {s[:4]}"
def lever(n):
    r=g(f"https://api.lever.co/v0/postings/{n}?mode=json")
    if r and r.status_code==200:
        js=r.json(); s=[j["text"] for j in js if STU.search(j["text"])]
        if js: return f"LEVER {n} {len(js)} | stu {len(s)} | {s[:4]}"
def ashby(n):
    r=g(f"https://api.ashbyhq.com/posting-api/job-board/{n}")
    if r and r.status_code==200:
        js=r.json().get("jobs",[]); s=[j["title"] for j in js if STU.search(j["title"])]
        if js: return f"ASHBY {n} {len(js)} | stu {len(s)} | {s[:4]}"
def sr(n):
    out=[]
    for v in {n, n.capitalize(), n.upper()}:
        r=g(f"https://api.smartrecruiters.com/v1/companies/{v}/postings?limit=100")
        if r and r.status_code==200:
            js=r.json().get("content",[]); tot=r.json().get("totalFound",0)
            if tot: s=[j["name"] for j in js if STU.search(j["name"])]; return f"SR {v} {tot} | stu {len(s)} | {s[:4]}"
def workable(n):
    r=g(f"https://apply.workable.com/api/v1/widget/accounts/{n}")
    if r and r.status_code==200:
        js=r.json().get("jobs",[]); s=[j["title"] for j in js if STU.search(j["title"])]
        if js: return f"WORKABLE {n} {len(js)} | stu {len(s)} | {s[:4]}"
with cf.ThreadPoolExecutor(20) as ex:
    for f in (gh,lever,ashby,sr,workable):
        for o in ex.map(f,names):
            if o: print(o,flush=True)
# Workday : lentement
WD=[("blackstone.wd1.myworkdayjobs.com","blackstone","Blackstone_Campus_Careers"),("hl.wd1.myworkdayjobs.com","hl","Campus"),
    ("db.wd3.myworkdayjobs.com","db","DBWebsite"),("ubs.wd3.myworkdayjobs.com","ubs","UBS_Graduates_and_Interns"),
    ("mq.wd3.myworkdayjobs.com","mq","CareersatMQ"),("wd1.myworkdaysite.com","wellsfargo","WellsFargoJobs")]
s=requests.Session()
for host,ten,site in WD:
    try: s.get(f"https://{host}/en-US/{site}",headers={"User-Agent":UA["User-Agent"]},timeout=20)
    except Exception: pass
    time.sleep(10)
    try:
        r=s.post(f"https://{host}/wday/cxs/{ten}/{site}/jobs",json={"appliedFacets":{},"limit":20,"offset":0,"searchText":"intern"},
                 headers={**UA,"Content-Type":"application/json","Origin":f"https://{host}","Referer":f"https://{host}/en-US/{site}"},timeout=30)
        print("WD",ten,r.status_code, (r.json().get("total") if r.status_code==200 else r.text[:80]),flush=True)
    except Exception as e: print("WD",ten,"ERR",e)
