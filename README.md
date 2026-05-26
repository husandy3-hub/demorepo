# 俄罗斯方块（Python + pygame）

## 运行方式

```bash
cd 新文件_AI12334   # 或克隆后的项目目录
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python tetris.py
```

## 操作说明

- **← / →**：左右移动  
- **↑**：旋转  
- **↓**：加速下落（软降）  
- **空格**：直接落到底（硬降）  
- **R**：游戏结束后重新开始  
- **Esc**：退出  

## 依赖

`requirements.txt` 中列出了依赖（主要为 `pygame`），请使用上方命令创建虚拟环境并安装。
