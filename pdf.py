import pdfplumber  # 用于处理 PDF 文件
import chardet  # 用于检测文件编码


MAX_FILE_CONTENT = 20000  # 读取文件内容的最大字符数

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

# 运行示例
if __name__ == "__main__":
    # 假设 files 是上传的文件列表
    file_paths = [
        "downloaded_pdfs/How ‘organized looting and plunder’ drove Britain’s second scientific revolution.pdf",
    ]
    result = process_uploaded_files(file_paths)
    print(result)  # 打印处理结果
    # 打印结果的长度
    print(f"处理结果长度: {len(result)}")