import os

import uvicorn

'''
cd ~/mabi
source venv/bin/activate
nohup python run.py > server.log 2>&1 &
tail -n 50 server.log
'''
def main():
    # 플랫폼별 기본 PORT 관례(예: Heroku/Cloud Run)
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run("main:app", host=host, port=port)


if __name__ == "__main__":
    main()
