# academic-auto-tracker

## 功能说明与待办

- [x] 订阅Nature的RSS
- [x] 调用Deepseek API识别论文与‘我的兴趣’是否相关 -> 需要在[backend/app/main.py](backend/app/main.py)中个性化定义SYSTEM_prompt
- [x] 下载感兴趣的PDF文件（目前仅适配Nature期刊论文）
- [x] 将论文原文发送给Deekseek，返回4点核心内容
- [x] 基于论文原文的简单问答（仅后端）
- [ ] 将设置“我的兴趣”prompt移到前端
- [ ] 扩展RSS来源，或使用semantic scholar的API
- [ ] 是否需要将PDF原文内容全部存到数据库（数据量会比较大？）
- [ ] 基于PDF原文的多轮上下文对话功能，增加Figure识别功能
- [ ] 支持调用本地大模型
- [ ] 论文数量足够之后训练本地的微调大模型或者做一个RAG应用
- [ ] 前端美化

## 使用说明

### 基于FastAPI的后端部署。

1. 查看[backend/app/main.py](backend/app/main.py),安装必要的Python库。（比较懒还没写requirements）。

2. 安装Postgres，并执行[backend/create_table.sql](backend/create_table.sql)来创建表格。

3. 在`backend/app`目录下面新建`.env`文件，并添加数据库密码等敏感信息。

4. 使用uvicorn启动后端。

### 基于React的前端部署

1. 在frontend目录下执行`npm install`可以直接安装所有依赖。

2. 执行`npm start`开启前端测试。

**需要注意的是，[frontend/src/api.js](frontend/src/api.js)等文件中的后端地址指向了我在云服务器中的地址，需要手动更改成你的后端地址。**

