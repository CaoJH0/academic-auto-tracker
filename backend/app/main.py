from fastapi import FastAPI, Response, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import requests
import logging
import pdfplumber
import chardet
import json
from typing import List, Dict, Union
import feedparser
import oss2
from dotenv import load_dotenv
import os
from pydantic import BaseModel

# 加载环境变量
load_dotenv()

# 创建 FastAPI 实例
app = FastAPI()

# 在 FastAPI 实例化后添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源 (安全性问题)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 连接到 PostgreSQL 数据库
while True:
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="academic_auto_tracker",
            user='postgres',
            password=os.getenv("postgres_password"),  # 从环境变量获取密码
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        print("Database connection was successful")
        break
    except Exception as error:
        print("Connection to database failed")
        print("Error: ", error)
        time.sleep(2)

# 配置常量
API_URL = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek API 的 URL
api_key = os.getenv("api_key") 
MAX_CONTEXT_MESSAGES = 8  # 最大上下文消息数
MAX_FILE_CONTENT = 30000  # 读取文件内容的最大字符数
# 阿里云 OSS 配置
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
OSS_ENDPOINT = 'http://oss-cn-hangzhou.aliyuncs.com'
OSS_BUCKET_NAME = 'academic-auto-tracker'
auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)


# 配置日志
LOG_FILENAME = "deepseek_dashboard.log"
logging.basicConfig(level=logging.INFO, filename=LOG_FILENAME, 
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DeepSeekDashboard")

# 从 RSS 源获取最新论文信息
# 同时自动获取PDF文件并从Deepseek获取关键信息
@app.post("/fetch_papers")
def fetch_papers():
    rss_url = "https://www.nature.com/nature.rss"  # 替换为您的 RSS 源
    feed = feedparser.parse(rss_url)

    for item in feed.entries:
        title = item.get("title")
        authors = ", ".join(author["name"] for author in item.get("authors", [])) # type: ignore
        prism_doi = item.get("prism_doi")
        prism_url = item.get("prism_url")
        summary = item.get("summary")
        journal = item.get("prism_publicationname")
        published_date = item.get("updated")
        
        # 检查是否已存在于数据库
        cursor.execute("SELECT * FROM papers WHERE doi = %s", (prism_doi,))
        if cursor.fetchone() is not None:
            continue  # 如果已存在，则跳过

        paper_check_system_prompt = """
        你是一个学术论文助手，用户会提供一篇文章的基本信息。请你根据这些信息判断文章是否与生态学研究相关，并且推断文章的类型（例如：研究性论文article、综述review、新闻news或者其他other）。
        如果文章与生态学研究相关，请返回“true”，否则返回“false”。以JSON格式输出英文。
        输出示例:
        标题: "Are groundbreaking science discoveries becoming harder to find?",作者: [{"name": "David Matthews"}],摘要: "<p>Nature, Published online: 21 May 2025; <a href=\"https://www.nature.com/articles/d41586-025-01548-4\">doi:10.1038/d41586-025-01548-4</a></p>Researchers are arguing over whether ‘disruptive’ or ‘novel’ science is waning – and how to remedy the problem.".
        输出示例: 
        {
        "is_related": false,
        "type": "other"
        }
        """
        paper_check_user_prompt = f"标题：{title}\n作者：{authors}\n摘要：{summary}"
        paper_checkr = query_deepseek(paper_check_user_prompt, paper_check_system_prompt, api_key, model="deepseek-chat", temperature=0)
        if paper_checkr is not None:
            try:
                # 将文本按行分割
                lines = paper_checkr.splitlines() # type: ignore
                # 去掉第一行和最后一行
                new_text = ''.join(lines[1:-1])
                paper_check_dict = json.loads(new_text)
                is_related = paper_check_dict.get("is_related")
                paper_type = paper_check_dict.get("type")
            except Exception as e:
                is_related = False
                paper_type = "unknown"
                logger.error(f"Failed to parse DeepSeek response: {e}")
        else:
            is_related = False
            paper_type = "unknown"

        cursor.execute("""
            INSERT INTO papers (title, authors, doi, url, summary, journal, is_related, type, published_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING title, doi;
        """, (title, authors, prism_doi, prism_url, summary, journal, is_related, paper_type, published_date))
        new_paper = cursor.fetchone()
        logger.info(f"Fetched paper: {new_paper}")
        
    conn.commit()
    return {"message": "Papers fetched and stored successfully."}

# 更新数据库中的论文类型，及其与指定研究领域的相关性
@app.patch("/update_paper_check")
def update_paper_check():
    cursor.execute("""
                   SELECT * FROM papers WHERE type = 'unknown'
                   """)
    papers = cursor.fetchall()

    update_number = 0

    for paper in papers:
        title = paper["title"] # type: ignore
        authors = paper["authors"] # type: ignore
        summary = paper["summary"] # type: ignore
        doi = paper["doi"] # type: ignore

        paper_check_system_prompt = """
        你是一个学术论文助手，用户会提供一篇文章的基本信息。请你根据这些信息判断文章是否与生态学研究相关，并且推断文章的类型（例如：研究性论文article、综述review、新闻news或者其他other）。
        如果文章与生态学研究相关，请返回“true”，否则返回“false”。以JSON格式输出英文。
        输出示例:
        标题: "Are groundbreaking science discoveries becoming harder to find?",作者: [{"name": "David Matthews"}],摘要: "<p>Nature, Published online: 21 May 2025; <a href=\"https://www.nature.com/articles/d41586-025-01548-4\">doi:10.1038/d41586-025-01548-4</a></p>Researchers are arguing over whether ‘disruptive’ or ‘novel’ science is waning – and how to remedy the problem.".
        输出示例: 
        {
        "is_related": false,
        "type": "other"
        }
        """
        paper_check_user_prompt = f"标题：{title}\n作者：{authors}\n摘要：{summary}"
        paper_checkr = query_deepseek(paper_check_user_prompt, paper_check_system_prompt, api_key, model="deepseek-chat", temperature=0)
        if paper_checkr is not None:
            try:
                # 将文本按行分割
                lines = paper_checkr.splitlines() # type: ignore
                # 去掉第一行和最后一行
                new_text = ''.join(lines[1:-1])
                paper_check_dict = json.loads(new_text)
                is_related = paper_check_dict.get("is_related")
                paper_type = paper_check_dict.get("type")
                # 更新数据库中的相关性和类型
                cursor.execute("""
                    UPDATE papers
                    SET is_related = %s, type = %s
                    WHERE doi = %s
                """, (is_related, paper_type, doi))
                update_number += 1
                logger.info(f"Checking relationship and type of paper : {title}")
            except Exception as e:
                is_related = False
                paper_type = "unknown"
                logger.error(f"Failed to parse DeepSeek response: {e}")
        else:
            is_related = False
            paper_type = "unknown"
    conn.commit()
    logger.info(f"Checked {update_number} papers successfully.")
    return {"message": f"{update_number} papers checked successfully."}

# 下载 PDF 文件
def download_pdf(url: str, save_path: str):
    try:
        response = requests.get(url, timeout=20)  # 设置超时时间
        response.raise_for_status()  # 检查请求是否成功

        # 保存 PDF 文件
        with open(save_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Downloaded PDF from {url} to {save_path}")
        return "success"

    except requests.ConnectionError:
        print(f"下载未完成: {url} - 网络连接错误")
        return "download_incomplete"  # 下载中断错误
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            print(f"无法下载: {url} - URL 不存在")
            return "url_not_found"  # URL 不存在错误
        else:
            print(f"下载失败: {url} - {e}")
            return "undownloaded"  # 其他 HTTP 错误
    except requests.Timeout:
        print(f"下载未完成: {url} - 请求超时")
        return "download_incomplete"  # 请求超时错误
    except Exception as e:
        print(f"发生错误: {e}")
        return "undownloaded"  # 其他错误

# 批量下载PDF文件
@app.patch("/download_pdfs")
def download_pdfs():
    # 获取所有未下载的论文
    cursor.execute("""
                   SELECT * FROM papers WHERE is_downloaded IN ('undownloaded', 'download_incomplete') AND is_related = TRUE
    """)
    papers = cursor.fetchall()
    download_number = 0

    for paper in papers:
        title = paper["title"] # type: ignore
        doi = paper["doi"]  # type: ignore
        url = paper["url"]  # type: ignore

        pdf_url = url + ".pdf"  # 假设 PDF 文件的 URL 是在原始 URL 后加上 ".pdf"
        pdf_path = f"./downloaded_pdfs/{title}.pdf"
        download_state = download_pdf(pdf_url, pdf_path)

        if download_state == "success":
            # 更新数据库中的 PDF 路径
            cursor.execute("""
                           UPDATE papers SET pdf_path = %s, is_downloaded = %s WHERE doi = %s
                           """, (pdf_path, 'success', doi))
            download_number += 1
        else :
            # 更新数据库中的 PDF 路径
            cursor.execute("""
                           UPDATE papers SET is_downloaded = %s WHERE doi = %s
                           """, (download_state, doi))
        
    conn.commit()
    return {"message": f"{download_number} PDF files downloaded successfully."}

# 上传 PDF 文件到阿里云 OSS
@app.patch("/upload_pdfs")
def upload_pdf():
    """上传 PDF 文件到阿里云 OSS，并返回文件的 URL。
    """
    cursor.execute("""
                   SELECT * FROM papers WHERE is_downloaded = 'success' AND is_uploaded = false
    """)
    papers = cursor.fetchall()

    for paper in papers:
        title = paper["title"] # type: ignore
        doi = paper["doi"] # type: ignore
        pdf_path = './downloaded_pdfs/'+title+'.pdf'  # type: ignore
        key = doi+'.pdf'  # type: ignore
        try:
            # 上传文件到 OSS
            result = bucket.put_object(key, open(pdf_path, 'rb'))
            if result.status == 200:
                logger.info(f"Uploaded {pdf_path} to OSS successfully.")
                # 更新数据库中的 PDF 路径
                cursor.execute("""
                               UPDATE papers SET pdf_path = %s, is_uploaded = true WHERE doi = %s
                               """, (key, doi))
            else:
                raise HTTPException(status_code=500, detail=f"Failed to upload file {pdf_path} to OSS,1")
        except Exception as e:
            logger.error(f"Failed to upload {pdf_path} to OSS: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file {pdf_path} to OSS,2")
    conn.commit()
    return {"message": "PDF files uploaded successfully."}


# 请求 DeepSeek API 处理 PDF 文件
@app.patch("/request_key_info")
def request_key_info():
    cursor.execute("""
                   SELECT * FROM papers WHERE is_downloaded = 'success' AND is_requested = false
    """)
    papers = cursor.fetchall()
    if not papers:
        raise HTTPException(status_code=404, detail="Paper not found")
    else:
        for paper in papers:
            pdf_path = [paper["pdf_path"],] # type: ignore
            doi = paper["doi"] # type: ignore

            pdf_content = process_uploaded_files(pdf_path)  # type: ignore # 提取 PDF 内容
            # 打印pdf内容前100个字符
            logger.info(f"PDF content for {doi}: {pdf_content[:100]}...")  # type: ignore
            print(f"PDF content for {doi}: {pdf_content[:100]}...")  # type: ignore
            system_prompt = """
            你是一个学术论文助手，用户会提供一篇文章的全文内容。请你对全文进行概括总结，写出4个最亮眼的内容摘要，每一条都需要包含文章结构+亮点概要。以JSON格式输出英文。
            输出示例:
            {
                "key_info_1": "result: content",
                "key_info_2": "result: content",
                "key_info_3": "result: content",
                "key_info_4": "result: content"
            }
            """

            key_info = query_deepseek(pdf_content, system_prompt, api_key, model="deepseek-chat", temperature=0)


            if key_info is not None:
                try:
                    # 将文本按行分割
                    lines = key_info.splitlines() # type: ignore
                    # 去掉第一行和最后一行
                    new_text = ''.join(lines[1:-1])
                    cursor.execute("""
                        UPDATE papers
                        SET key_info = %s, is_requested = TRUE
                        WHERE doi = %s
                    """, (new_text, doi))
                    logger.info(f"Key information for paper {doi} updated successfully.")
                except Exception as e:
                    logger.error(f"Failed to parse DeepSeek response: {e}")

    conn.commit()
    return {"message": "key information requested successfully."}


# 处理上传文件
def process_uploaded_files(file_paths) -> str:
    """处理上传的文件，提取文本内容并返回处理后的结果。
    
    Args:
        file_paths (list): 上传的文件列表。
    
    Returns:
        str: 提取的文件内容。
    """
    processed_content = []  # 存储处理后的内容
    for file_path in file_paths:
        try:
            if file_path.endswith(".pdf"):
                # 使用 pdfplumber 处理 PDF 文件
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""  # 提取每一页的文本
                processed_content.append(f"PDF_CONTENT:{file_path}: {text[:MAX_FILE_CONTENT]}...")  # 保存 PDF 内容
            else:
                # 自动检测文本文件编码
                with open(file_path, 'rb') as f:
                    raw_data = f.read()  # 读取文件
                    detected_encoding = chardet.detect(raw_data)  # 检测文件编码
                    encoding = detected_encoding.get("encoding", "utf-8-sig")  # type: ignore # 默认使用 utf-8-sig
                    content = raw_data.decode(encoding, errors="replace")  # 解码文件内容
                    processed_content.append(f"FILE_CONTENT:{file_path}: {content[:MAX_FILE_CONTENT]}...")  # 保存文本内容
        except Exception as e:
            processed_content.append(f"ERROR: 处理文件 {file_path} 时出错: {str(e)}")  # 提示用户错误
    return "\n".join(processed_content)  # 返回处理后的内容

# DeepSeek API 请求
def query_deepseek(prompt: str, system_prompt: str, api_key: str, model: str = "deepseek-chat",
                   temperature: float = 0.7) -> Union[Dict, None]:
    """向 DeepSeek API 发送请求并获取响应。
    
    Args:
        prompt (str): 用户的输入提示。
        system_prompt (str): 系统角色描述。
        api_key (str): 用户的 DeepSeek API 密钥。
        model (str, optional): 使用的模型名称。默认为 'deepseek-chat'。
        temperature (float, optional): 控制生成的创造力级别，默认值为 0.7。
    
    Returns:
        Union[Dict, None]: 返回 API 响应数据字典或 None。
    """
    headers = {
        "Authorization": f"Bearer {api_key}",  # 使用提供的 API 密钥进行身份验证
        "Content-Type": "application/json",  # 设置请求内容类型
        #'Accept': 'application/json',  # 设置接受的响应类型
    }

    try:
        # 构建请求负载
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}] + [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        logger.info(f"发送 {len(payload['messages'])} 条消息到 DeepSeek API...")  # 记录发送的消息数量

        response = requests.post(API_URL, headers=headers, json=payload)  # 发送 POST 请求
        response.raise_for_status()  # 检查请求是否成功

        if response.status_code == 200:
            response_data = response.json()  # 解析 JSON 响应
            assistant_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

            return assistant_response  # 返回助手的响应内容

        logger.error(f"API 返回了非 200 状态: {response.status_code}")  # 记录错误状态
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API 请求失败: {str(e)}", exc_info=True)  # 记录请求异常
        return None  # 返回 None 表示请求失败

@app.get("/papers")
def get_papers(skip: int = 0, limit: int = 20):
    cursor.execute("""
                   SELECT * FROM papers WHERE is_downloaded = 'success' AND is_requested = true
                   ORDER BY published_date DESC
                   OFFSET %s LIMIT %s
                   """, (skip, limit))
    papers = cursor.fetchall()
    if not papers:
        raise HTTPException(status_code=404, detail="Paper not found")
    else:
        return papers

class Paper(BaseModel):
    doi: str
    my_question: str

@app.get("/papers/paper")
def get_paper_by_title(paper: Paper):
    doi = paper.doi
    my_question = paper.my_question
    cursor.execute("""
                   SELECT * FROM papers WHERE doi = %s
                   """, (doi,))
    paper_meta = cursor.fetchone()

    pdf_path = [paper_meta["pdf_path"],]
    pdf_content = process_uploaded_files(pdf_path)  # type: ignore # 提取 PDF 内容
    # 打印pdf内容前100个字符
    logger.info(f"PDF content for {doi}: {pdf_content[:100]}...")  # type: ignore
    print(f"PDF content for {doi}: {pdf_content[:1000]}...")  # type: ignore

    system_prompt = """
            你是一个学术论文助手，用户会提供一个问题和一篇文章的全文内容。请你根据全文内容回答用户的问题。以JSON格式输出英文，按点列出，最多5点。
            输出示例:
            {
                "1. ": "key_info: content",
                "2. ": "key_info: content",
                "3. ": "key_info: content",
                "4. ": "key_info: content",
                "5. ": "key_info: content"
            }
            """
    user_prompt = f"问题：{my_question}\n全文内容：{pdf_content}"
    answer = query_deepseek(user_prompt, system_prompt, api_key, model="deepseek-chat", temperature=0)
    if answer is not None:
                try:
                    # 将文本按行分割
                    lines = answer.splitlines() # type: ignore
                    # 去掉第一行和最后一行
                    new_text = ''.join(lines[1:-1])
                    logger.info(f"Key information for paper {doi} updated successfully.")
                    answer_dict = json.loads(new_text)
                except Exception as e:
                    logger.error(f"Failed to parse DeepSeek response: {e}")
    return answer_dict