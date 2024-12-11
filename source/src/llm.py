import requests
import json
from openai import OpenAI

def read_keys_json():
    with open('<your_keys_json>') as f:
        keys = json.load(f)
    return keys

g_openai_client = read_keys_json()['openai']
openai_client = OpenAI(api_key=g_openai_client["api_key"], base_url=g_openai_client["base_url"])

def build_prompt(text: str):
    json_format = """{"keywords": [keyword1, ...], "five_points": "["<point1>", "<point2>", "<point3>", "<point4>", "<point5>"]", "score":"["<boring/normal/interesting>", "<boring/normal/interesting>"]"}"""
    example_output = """{
  "keywords": ["Fault Localization", "Large Language Models", "Query Reformulation", "Learning-to-Rank", "Bug Report Analysis"],
  "five_points": [
    "1. Explores the use of Information Retrieval for pinpointing software faults, highlighting existing methods' proficiency in source file ranking.",
    "2. Identifies issues with current IRFL methods in accurately parsing bug reports and constructing effective queries, leading to information loss.",
    "3. Proposes a novel method (LLmiRQ) that categorizes bug reports into programming entities, stack traces, and natural language for precise query formulation.",
    "4. Implements LLmiRQ+ for interactive query reformulation and a learning-to-rank model using features like class name matches and call graph scores to refine search results.",
    "5. Integrates advanced large language models to enhance fault localization accuracy, achieving superior performance metrics over seven state-of-the-art techniques."
  ],
    "score": ["interesting", "boring"]
}"""
    prompt = f"""
    ### Instruction
    Below is the title and abstract of a paper. Your task is to summarize what this paper does in a few bullet points, each around 50 words, including: 

1. What is the background of the research? 
2.  What are the main problems/challenges addressed in this paper? 
3.  What methods does the paper propose to address these issues/challenges? 
4. How does the paper implement these methods? 
5. What is the novelty of this paper?

Furthermore, extract up to five keywords from the paper that are more representative of its specific content, avoiding common terms like 'computer' or 'software engineering' that do not distinctly capture the essence of the work.

Last, give a score for the paper based on User Preference. The score can be 'boring', 'normal', or 'interesting'.
- boring: The paper is not interesting to the user.
- normal: The paper is somewhat interesting to the user.
- interesting: The paper is very interesting to the user.

### Output Format

```json
{json_format}
```

### Example
Input1:

User1 Preference: I have a particular interest in how large language models are applied within software engineering, especially software test, software bug with LLMs.

User2 Preference: I am interested in the application of machine learning.

Title: Enhancing IR-based Fault Localization using Large Language Models

Abstract: Information Retrieval-based Fault Localization (IRFL) techniques aim to identify source files containing the root causes of reported failures. While existing techniques excel in ranking source files, challenges persist in bug report analysis and query construction, leading to potential information loss. Leveraging large language models like GPT-4, this paper enhances IRFL by categorizing bug reports based on programming entities, stack traces, and natural language text. Tailored query strategies, the initial step in our approach (LLmiRQ), are applied to each category. To address inaccuracies in queries, we introduce a user and conversational-based query reformulation approach, termed LLmiRQ+. Additionally, to further enhance query utilization, we implement a learning-to-rank model that leverages key features such as class name match score and call graph score. This approach significantly improves the relevance and accuracy of queries. Evaluation on 46 projects with 6,340 bug reports yields an MRR of 0.6770 and MAP of 0.5118, surpassing seven state-of-the-art IRFL techniques, showcasing superior performance.

Output1:

```json
{example_output}
```

### Input:

{text}    
"""
    return prompt

def call_openai_api(prompt: str, format: str = "") -> any:
    """Call the OpenAI API to generate text based on the prompt.

    Args:
        prompt (str): User prompt.
        system_message (str): System message.
        format (str, optional): OpenAI model ouput format, only 'json' option. Defaults to "".

    Returns:
        any: The generated result.
    """
    response = openai_client.chat.completions.create(
            model=g_openai_client["model"],
            messages=[
                {'role': 'user', 
                'content': prompt},
            ],
            stream=False,
            temperature=0.7,
            top_p=1.0,
            n=1,
            max_tokens=4096,
            response_format={"type": "json_object"}
        )
    ret_json = {"keywords":[], "five_points":[], "score":[]}
    try:
        tmp = json.loads(response.choices[0].message.content)
        if "keywords" in tmp:
            ret_json["keywords"] = tmp["keywords"]
        if "five_points" in tmp:
            ret_json["five_points"] = tmp["five_points"]
        if "score" in tmp:
            ret_json["score"] = tmp["score"]
    except Exception as e:
        print(e)
        ret_json = response.choices[0].message.content
    return ret_json

if __name__ == "__main__":
    text = """
    User1 Preference: I have a particular interest in how large language models are applied within software engineering, especially software test with LLMs.
    User2 Preference: I am interested in the application of machine learning.
    Title: Leveraging Large Language Models to Generate Course-specific Semantically Annotated Learning Objects
    Abstract: Background: Over the past few decades, the process and methodology of automated question generation (AQG) have undergone significant transformations. Recent progress in generative natural language models has opened up new potential in the generation of educational content.
Objectives: This paper explores the potential of large language models (LLMs) for generating computer science questions that are sufficiently annotated for automatic learner model updates, are fully situated in the context of a particular course, and address the cognitive dimension understand.
Methods: Unlike previous attempts that might use basic methods like ChatGPT, our approach involves more targeted strategies such as retrieval-augmented generation (RAG) to produce contextually relevant and pedagogically meaningful learning objects.
Results and Conclusions: Our results show that generating structural, semantic annotations works well. However, this success was not reflected in the case of relational annotations. The quality of the generated questions often did not meet educational standards, highlighting that although LLMs can contribute to the pool of learning materials, their current level of performance requires significant human intervention to refine and validate the generated content."""
    a = call_openai_api(build_prompt(text))
    print(type(a))
    print(a)