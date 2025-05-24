import requests
import logging
import pdfplumber
import chardet
from typing import Union, Dict

# client = OpenAI(api_key="sk-d49eaad9e4694df4a44462f7043496f9", base_url="https://api.deepseek.com")

# response = client.chat.completions.create(
#     model="deepseek-chat",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant"},
#         {"role": "user", "content": "Hello, tell me about the some claasic research in AI."},
#     ],
#     stream=False,
#     file=
# )

# print(response.choices[0].message.content)

# 配置常量
API_URL = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek API 的 URL
LOG_FILENAME = "deepseek_dashboard.log"  # 日志文件名
MAX_CONTEXT_MESSAGES = 8  # 最大上下文消息数
MAX_FILE_CONTENT = 1000  # 读取文件内容的最大字符数

# 日志配置
def configure_logging():
    """配置日志记录器，设置日志格式和处理器。"""
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 创建文件处理器和控制台处理器
    file_handler = logging.FileHandler(LOG_FILENAME)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 配置基本的日志设置
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

# 调用日志配置函数
configure_logging()
logger = logging.getLogger("DeepSeekDashboard")  # 创建日志记录器

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
                    encoding = detected_encoding.get("encoding", "utf-8-sig")  # 默认使用 utf-8-sig
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

# 示例如何使用以上函数
if __name__ == "__main__":

    # files 是上传的文件列表
    files = [
        "downloaded_pdfs/How ‘organized looting and plunder’ drove Britain’s second scientific revolution.pdf",
        "downloaded_pdfs/Who were the ancient Denisovans? Fossils reveal secrets about the mysterious humans.pdf"
            ]

    # 处理上传的文件
    extracted_content = process_uploaded_files(files)
    print("提取的文件内容:")
    print(extracted_content)

    # 示例 DeepSeek API 请求
    api_key = "sk-d49eaad9e4694df4a44462f7043496f9"  # 请替换为您的实际 API 密钥
    system_prompt = """
        你是一个学术论文助手，用户会提供一篇文章的基本信息。请你根据这些信息判断文章是否与生态学研究相关，并且推断文章的类型（例如：研究性论文article、综述review、新闻news或者其他other）。
        如果文章与生态学研究相关，请返回“True”，否则返回“False”。以JSON格式输出英文。
        输出示例:
        标题: "Are groundbreaking science discoveries becoming harder to find?",作者: [{"name": "David Matthews"}],摘要: "<p>Nature, Published online: 21 May 2025; <a href=\"https://www.nature.com/articles/d41586-025-01548-4\">doi:10.1038/d41586-025-01548-4</a></p>Researchers are arguing over whether ‘disruptive’ or ‘novel’ science is waning – and how to remedy the problem.".
        输出示例: 
        {
        "is_related": False,
        "type": "other"
        }
        """
    user_prompt = "我会提供文件pdf给你，请你根据文件内容提炼出每个文件的核心内容"

    full_prompt = f"{user_prompt}\n{extracted_content}"  # 将提取的内容与用户提示结合

    response = query_deepseek(full_prompt, system_prompt, api_key, model="deepseek-chat", temperature=0)
    print("DeepSeek API 响应:")
    print(response)