import feedparser
import requests
import os

# 定义存储条目的列表
entries_list = []

# 解析 RSS feed
feed = feedparser.parse('https://www.nature.com/nature.rss')

# 创建一个存储 PDF 文件的文件夹
output_folder = 'downloaded_pdfs'
os.makedirs(output_folder, exist_ok=True)

# 提取条目并更新列表
for entry in feed.entries:
    doi = entry.dc_identifier.split(':')[-1]  # 从 DOI 字段中提取 DOI
    pdf_url = entry.link + '.pdf'  # 构造 PDF 链接

    # 检查条目是否已存在于列表中
    if any(e['doi'] == doi for e in entries_list):
        print(f"条目已存在，跳过下载: {entry.title} (DOI: {doi})")
        continue

    # 添加新条目到列表
    entries_list.append({'doi': doi, 'title': entry.title, 'is_download': False})

    # 下载 PDF 文件
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()  # 检查请求是否成功

        # 创建文件名
        file_name = os.path.join(output_folder, f"{entry.title}.pdf")

        # 保存 PDF 文件
        with open(file_name, 'wb') as pdf_file:
            pdf_file.write(response.content)

        # 更新条目状态为已下载
        for e in entries_list:
            if e['doi'] == doi:
                e['is_download'] = True
                
        print(f"成功下载: {file_name} (DOI: {doi})")
    except requests.HTTPError as e:
        print(f"下载失败: {pdf_url} - {e}")
    except Exception as e:
        print(f"发生错误: {e}")

# 打印当前下载列表
print("下载条目列表:")
for e in entries_list:
    print(f"DOI: {e['doi']}, Title: {e['title']}, Is Downloaded: {e['is_download']}")