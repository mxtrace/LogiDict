# -*- coding: utf-8 -*-
"""
写入 database.py 完整内容
"""
content = open(__file__).read()
# 找到 CONTENT_START 和 CONTENT_END 之间的内容
start = content.index("CONTENT_START") + len("CONTENT_START") + 1
end = content.index("CONTENT_END") - 1

db_code = content[start:end]
with open(r'C:\Users\miaoyua\Documents\LogiDict\database.py', 'w', encoding='utf-8') as f:
    f.write(db_code)
print(f'database.py 写入完成，{len(db_code)} 字节')

# CONTENT_START
