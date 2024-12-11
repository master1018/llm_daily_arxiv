import re
import time
import json
import datetime
import smtplib
import pytz
import outlook

keywords_dblp = ["large language model", "llm", "diagnosis", "incident", "cloud", "anomaly detection", "failure prediction"]

CN_TZ = pytz.timezone('Asia/Shanghai')

def generate_html(time_sorted_papers, queries):
    html_contests = []
    for i in range(0, len(queries)):
        query = queries[i]
        content = ""
        check_keywords = query["keywords"]
        check_domains = query["domains"]
        for paper in time_sorted_papers:
            if any(keyword.lower() in paper["keywords"].lower() for keyword in check_keywords) \
                and any(domain.lower() in paper["primary_category"].lower() for domain in check_domains):

                title = '<h3><a href="{}" target="_blank">{}</a></h3>'.format(
                    paper['pdf_link'], paper['title'])

                arxiv_link = '<p>arXiv link: <a href={0}>{0}</a></p>'.format(
                    paper["arxiv_link"])

                primary_category = '<p>Primary Category: <b>{}</b></p>'.format(
                    paper['primary_category'])

                suggestion_score = '<p>Suggestion Score: <b>{}</b></p>'.format(
                    paper['score'][i])

                journal_ref = ""
                if paper['journal_ref'] is not None:
                    journal_ref = "<p>Journal-ref: {}</p>".format(
                        paper['journal_ref'])

                authors = '<p><b>{}</b></p>'.format(paper['authors'])
                keywords_ = '<p>Keywords: <b>{}</b></p>'.format(paper['keywords'])
                #summary = '<p>{}<p>'.format(paper['summary'])
                summary = ""
                for s in paper['summary']:
                    summary += '<p>{}<p>'.format(s)
                #abstract = '<p>{}<p>'.format(paper['abstract'])
                for query in queries:
                    keywords = query["keywords"]
                    for keyword in keywords:
                        # abstract = abstract.replace(
                        #     keyword, "<b>" + keyword + "</b>")
                        summary = re.sub(
                            r"(%s)" % keyword, repl_func, summary, flags=re.IGNORECASE)

                new_paper = f"{title}{authors}{arxiv_link}{primary_category}{suggestion_score}{journal_ref}{keywords_}{summary}"

                new_paper = f'<div style="background-color: #f0f0f0; padding: 10px; margin-bottom: 10px;">{new_paper}</div>'
                content += '{}<br/>'.format(new_paper)

        html_content = f"<html><body>{content}</body></html>"

        html_contests.append(html_content)

    return html_contests

def generate_html_dblp(dblp_papers):
    content = ""
        # content += '<h2>{}</h2>'.format(time)
        
    # sort by keywords
    papers_info = []
    map_used = [0] * len(dblp_papers)
    for key in keywords_dblp:
        for i in range(0, len(dblp_papers)):
            if map_used[i] == 1:
                continue
            if key in dblp_papers[i]["title"].lower():
                map_used[i] = 1
                papers_info.append(dblp_papers[i])

    for paper in papers_info:
        title = '<h3><a href="{}" target="_blank">{}</a></h3>'.format(
            paper["href"], paper["title"])

        primary_category = '<p>Category: <b>{}</b></p>'.format(
            paper["ConOrJouName"])

        authors = '<p><b>{}</b></p>'.format(paper["authors"])

        new_paper = f"{title}{authors}{primary_category}"

        content += '{}<br/>'.format(new_paper)

    html_content = f"<html><body>{content}</body></html>"
    return html_content


def repl_func(match):
    return "<b><u>" + match.group() + "</u></b>"


def get_config(config_path="./config/basic.json"):
    try:
        with open(config_path, 'r', encoding='utf8') as fp:
            config = json.load(fp)

    except Exception:
        print('Please check config file.')
        print('Stoppend by error.')
        exit(-1)

    return config


def get_queries(query_path="./query.json"):
    try:
        with open(query_path, 'r', encoding='utf8') as fp:
            queries = json.load(fp)

    except Exception:
        print('Please check query file.')
        print('Stoppend by error.')
        exit(-1)

    return queries


def get_local_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))


def generate_subject(get_daily):
    today = datetime.date.today()
    
    if get_daily == True:
        subject = f"[arXiv] Paper Summary {today}"
        return subject
    
    pastweek_day = today + datetime.timedelta(days=-7)

    subject = f"[arXiv] Paper Summary {pastweek_day}~{today}"

    return subject

def generate_subject_dblp():
    today = datetime.date.today()
    
    pastweek_day = today + datetime.timedelta(days=-7)

    subject = f"[dblp] Paper Summary {pastweek_day}~{today}"

    return subject

def send_mails(mail_config, subject, contents):
    try:
        if not mail_config["enable"]:
            return

        mail = outlook.Outlook(mail_config)
        mail.login(mail_config["sender"], mail_config["auth"])

        for i in range(0, len(mail_config["receivers"])):
            receiver = mail_config["receivers"][i]
            content = contents[i]
            print(f"send to {receiver}")
            mail.sendEmail(receiver, subject, content)

    except smtplib.SMTPException:
        print(get_local_time(), 'Mail send failed!')

    else:
        print(get_local_time(), 'Mail send succeeded!')


def get_next_send_wait_seconds(config):
    if not config["enable"]:
        return datetime.datetime.now().astimezone(CN_TZ), 0

    weekday_next_time, weekday_wait_seconds = get_next_weekday_datetime_wait_seconds(
        config["weekday"], config["hour"])
    duration_next_time, duration_wait_seconds = get_duration_wait_seconds(
        config["duration"], config["hour"])
    if weekday_wait_seconds <= duration_wait_seconds:
        return weekday_next_time, weekday_wait_seconds

    return duration_next_time, duration_wait_seconds


def get_next_weekday_datetime_wait_seconds(weekday, hour=0, minute=0, second=0, d=datetime.datetime.now()):
    delta = weekday - d.isoweekday()
    if delta <= 0:
        delta += 7

    dt = d + datetime.timedelta(delta)

    dt = dt.replace(hour=hour)
    dt = dt.replace(minute=minute)
    dt = dt.replace(second=second, microsecond=0)

    wait_seconds = (dt - d).total_seconds()

    return dt, wait_seconds


def get_duration_wait_seconds(duration, hour=0, minute=0, second=0, d=datetime.datetime.now()):
    if duration <= 0:
        duration += 7

    dt = d + datetime.timedelta(duration)

    dt = dt.replace(hour=hour)
    dt = dt.replace(minute=minute)
    dt = dt.replace(second=second, microsecond=0)

    wait_seconds = (dt - d).total_seconds()

    return dt, wait_seconds
