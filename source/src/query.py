import re
import arxiv
import requests
import utils
import datetime
import pytz
import json
from llm import call_openai_api, build_prompt

first_papers = {}

CN_TZ = pytz.timezone('Asia/Shanghai')


def str_to_datetime(str_date):
    return datetime.datetime.strptime(str_date, "%Y%m%d")

def query_weekly_paper(config):
    queries = utils.get_queries(config["queries"])
    
    global first_papers

    #init first papers
    first_papers = {}
    
    for query in queries:
        domains = query['domains']
        for domain in domains:
            if domain not in first_papers:
                first_papers[domain] = ""
    sum_query = {"keywords": [], "domains": [], "preference": []}

    for query in queries:
        sum_query["keywords"].extend(query["keywords"])
        sum_query["domains"].extend(query["domains"])
        sum_query["preference"].append(query["preference"])
    sum_query["keywords"] = list(set(sum_query["keywords"]))
    sum_query["domains"] = list(set(sum_query["domains"]))

    print("first paper start")
    print(first_papers)
    paper_infos = get_weekly_papers(
        [sum_query], config["entry_per_page"], config["get_daily"])
    print("first paper final")
    print(first_papers)

    if paper_infos != []:
        with open("last_arxiv.json", "w") as f:
            f.write(json.dumps(first_papers))

    if paper_infos == [] or len(paper_infos) == 0:
        print("no paper query")
        return
    contents = utils.generate_html(paper_infos, queries)
    subject = utils.generate_subject(config["get_daily"])
    utils.send_mails(config["mail"], subject, contents)

def deduplicate_list(input_list):
    seen_values = set()
    result_list = []
    check_val = []
    for item in input_list:
        value = item['title']

        if value not in seen_values:
            seen_values.add(value)
            result_list.append(item)
            check_val.append(value)

    return result_list


def get_weekly_papers(queries: dict, step: int = 120, get_daily: bool = False):
    paper_infos = []

    today = datetime.datetime.today()
    day_of_week = today.weekday() + 1
    #if day_of_week == 6 or day_of_week == 7:
    #    return []
    if get_daily == True:
        print("Query for {0} papers".format(today))

    for query in queries:
        keywords = query["keywords"]
        domains = query["domains"]

        print(utils.get_local_time(), "Query keywords:", keywords)
        print(utils.get_local_time(), "Query domains:", domains)

        for keyword in keywords:
            keyword = keyword.lower()

        for domain in domains:
            query_url = f"https://arxiv.org/list/{domain}/pastweek"
            base_link = query_url + f"?show={step}"

            link = base_link
            page_content = get_page_content(link)
            new_papers_info = get_related_papers_from_content(
                page_content, keywords, domain, query["preference"])
            print("new papers info: ", len(new_papers_info))
            paper_infos.extend(new_papers_info)

  

    return paper_infos



def get_page_content(link: str):
    print("Query past week list:", link)
    return requests.get(link).content.decode('utf-8').split('\n')


def get_max_entries_from_content(page_content):
    max_entries = 120
    for item in page_content:
        r = r'total of (\d*) entries'
        m = re.search(r, item)
        if m:
            try:
                max_entries = int(m.group(1))

            except:
                print("Didn't find max_entries, use the default value (120).")

            break

    return max_entries


def get_arxiv_ids_from_content(page_content):
    arxiv_ids = []
   
    for item in page_content:
        r = r'href="/pdf/(\d*.\d*)"'
        m = re.search(r, item)
        if m:
          #  print(m)
            arxiv_ids.append(m.group(1))
    return arxiv_ids


def is_related(abstract, keywords):
    related_flag = False
    topic = ""
    for keyword in keywords:
        if keyword in abstract.lower():
            related_flag = True
            topic = keyword
    return related_flag, topic


def get_related_papers_from_content(page_content, keywords, domain, preference = ""):
    last_papers = {}

    try:
        with open("last_arxiv.json") as f:
            last_papers = json.load(f)
    except Exception:
        print("[WARING] exception when read the last_arixiv.json")
        last_papers = {}
    global first_papers

    paper_infos = []

    arxiv_ids = get_arxiv_ids_from_content(page_content)
    papers = arxiv.Search(id_list=arxiv_ids)
    for paper in papers.results():
        if first_papers[domain] == "":
            first_papers[domain] = paper.title
           # print(first_papers)

        if domain not in last_papers:
            last_papers[domain] = ""

        elif last_papers[domain] == paper.title:
            break
            
        abstract = paper.summary
        abstract = re.sub(r'\n {2}', r'\n###', abstract)
        abstract = re.sub(r'\n', r' ', abstract)
        abstract = re.sub(r'###', r'\n', abstract)
        
        check_val, topic = is_related(abstract, keywords)
        if paper.primary_category != domain:
            continue

        if check_val:
            input_text = ""

            for i in range(0, len(preference)):
                input_text += f"""
                User{i + 1} Preference: {preference}
                """

            input_text += f"""
            Title: {paper.title}
            Abstract: {abstract}
            """
            retry_times = 0
            while True:
                llm_answer = call_openai_api(build_prompt(input_text))
                try:
                    keywords = ""
                    five_points = ""
                    if type(llm_answer["keywords"]) == list:
                        keywords = ', '.join(llm_answer["keywords"])
                    else:
                        keywords = llm_answer["keywords"]
                    if type(llm_answer["five_points"]) == list:
                        five_points = [it for it in llm_answer["five_points"]]
                    else:
                        five_points = [llm_answer["five_points"]]
                    paper_info = {
                        'time': str(paper.updated.year).zfill(4) + str(paper.updated.month).zfill(2) + str(
                            paper.updated.day).zfill(2), 'title': paper.title,
                        'pdf_link': str(paper.links[-1]),
                        "arxiv_link": str(paper.links[0]),
                        'authors': ', '.join([author.name for author in paper.authors]),
                        'abstract': abstract,
                        'primary_category': paper.primary_category,
                        'journal_ref': paper.journal_ref,
                        'topic': topic,
                        'keywords': keywords,
                        'summary': five_points,
                        'score': llm_answer["score"]
                    }
                    paper_infos.append(paper_info)
                    break
                except Exception as e:
                    retry_times += 1
                    if retry_times > 3:
                        print("retry times > 3")
                        print(e)
                        print(type(llm_answer))
                        print(input)
                        print(llm_answer)
                        break
                    print("retry times: ", retry_times)

    return paper_infos
