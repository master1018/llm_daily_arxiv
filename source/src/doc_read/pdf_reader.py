import subprocess
import os

class ArxivPdfReader():
    def __init__(self, arxiv_pdf_link):
        self.arxiv_pdf_link = arxiv_pdf_link
        self.result = ""
        
        self.download_pdf(arxiv_pdf_link)
        self.magic_pdf_process()
        self.result = self.convert2json()

    def get_parse_result(self):
        return self.result

    def convert2json(self):
        magic_output = "/tmp/magic-pdf/tmp/txt/tmp.md"

        paper_contents_full = {}

        with open(magic_output, "r") as f:
            lines = f.readlines()
        
        for i in range(len(lines)):
            cur_line = lines[i]
            # check if the cur line is section 
            if cur_line.startswith("# "):
                section_name = cur_line
                paper_contents_full[section_name] = ""
                for j in range(i+1, len(lines)):
                    if lines[j].startswith("# "):
                        break
                    paper_contents_full[section_name] += lines[j]
                i = j
            else:
                i += 1
            
        paper_contents = []

        flag = 0
        for key in paper_contents_full.keys():
            if "Introduction".lower() in key.lower():
                flag = 1
            if flag == 0:
                continue
            if "References".lower() in key.lower() or "Acknowledgement".lower() in key.lower():
                break
            paper_contents.append({"Section": key, "Content": paper_contents_full[key]})

        return paper_contents

    def magic_pdf_process(self):
        result = subprocess.run(
            ["magic-pdf", "pdf-command","--pdf", "./tmp.pdf", "--inside_model", "True", "--model_mode", "lite", "--method", "txt"],
            capture_output=True,
            text=True
        )

    def download_pdf(self, arxiv_pdf_link: str):
        os.system(f"wget {arxiv_pdf_link} -O ./tmp.pdf")

    def delete_pdf(self):
        os.system("rm ./tmp.pdf")

    def delete_magic_output(self):
        os.system("rm ./tmp.txt")


test_link = "https://arxiv.org/pdf/2412.08615v1"

reader = ArxivPdfReader(test_link)

res = reader.get_parse_result()

for r in res:
    print(r)