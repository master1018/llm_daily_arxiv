# Daily auto check arxiv papers

An arXiv paper email sender with LLM in.

## Dependency

```shell
pip install arxiv
pip install openai
pip install apscheduler
```

## Configuration

Create and modify `basic.json` & `query.json` `keys.json`.

### basic.json

```json
{
    "task": {
        "enable": true,                         // When set to true, it will run on a schedule, 
                                                // otherwise it will run temporarily.
        "weekday": 1,                           // The numbers 1-7 represent Monday through Sunday.
        "hour": 9,                              // The hour in the 24-hour clock.
        "duration": 7                           // The number of days between automatic task intervals.
    },
    "queries": "./config/query.json",           // The file path for the query keywords and domains.
    "entry_per_page": 120,                      // The number of documents retrieved per query.
    "mail": {
        "enable": true,                         // When set to true, an email will be sent.
        "sender": "xxx@outlook.com",            // The email address to be used for sending emails.
        "auth": "xxxxxxxx",                     // The authentication code corresponding to the sender.
        "receivers": [
            "xxx@outlook.com"                   // Multiple email addresses can be used for receiving emails.
        ],
        "imap_server": "imap-mail.outlook.com", // The following are the settings for Outlook email. 
        "imap_port": 993,                       // Please set up accordingly for other email providers.
        "smtp_server": "smtp-mail.outlook.com",
        "smtp_port": 587
    }
}
```

> The authentication code needs to correspond with the sending email address. 
> Please refer to the email service's instructions for more information.
> For Outlook, pleas check [How to create a new app password](https://support.microsoft.com/en-us/account-billing/using-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944#ID0EDT).
>
> QQ email is also useful.

### query.json

```json
[
    {
        "keywords": [                 // The keywords to be searched.
            "large language model",
            "anomaly detection",
        ],
        "domains": [                  // The domain to be searched.
            "cs.SE",                  // Please refer to the arXiv website          
            "cs.CR"                   // for the code corresponding to the domain.
        ],
      	"preference":"I have a particular interest in LLMs, especially LLMs apply in software engineering."
    }
]
```

### Keys.json

```json
{
    "openai": {
        "api_key": "",
        "base_url": "",
        "model": ""
    }
}
```
And you should also modify llm.py:

```python
def read_keys_json():
    with open('<your_keys_json>') as f:
        keys = json.load(f)
    return keys
```
## Run

```shell
cd source
nohup python -u src/check_paper.py > log.txt &
```

## Refs

https://github.com/forestneo/weekly-papers-in-arXiv

https://github.com/awangga/outlook/



