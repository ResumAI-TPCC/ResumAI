import asyncio
import os
import sys
from pathlib import Path

# 添加 backend 目录到 python 路径
backend_dir = os.getcwd()
sys.path.append(backend_dir)

from fastapi import UploadFile
from io import BytesIO
from app.services.resume_service import upload_resume_to_gcs

async def run_test():
    print("🚀 开始真实上传测试...")
    
    # 模拟一个 UploadFile
    content = b"This is a test file for ResumAI GCS upload."
    file_io = BytesIO(content)
    
    # 创建模拟的 UploadFile 对象
    test_file = UploadFile(
        filename="connection_test.txt",
        file=file_io,
        headers={"content-type": "text/plain"}
    )
    
    try:
        result = await upload_resume_to_gcs(test_file)
        print("\n✅ 上传成功！")
        print(f"File ID: {result['file_id']}")
        print(f"Storage Path: {result['storage_path']}")
        print("\n请前往 Google Cloud Console 检查文件是否存在。")
    except Exception as e:
        print(f"\n❌ 上传失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_test())
