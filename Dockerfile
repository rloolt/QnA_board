# 파이썬이 미리 깔려있는 이미지를 가져옴
FROM python:3.9-slim

# 컨테이너 안에서 작업을 시작할 폴더 이름을 정함
WORKDIR /app

# 현재 내 폴더에 있는 모든 파일을 컨테이너 안으로 복사
COPY . .

# 복사된 requirements.txt를 보고 필요한 라이브러리를 설치
RUN pip install --no-cache-dir -r requirements.txt

# 서버 실행 명령어를 입력
CMD ["python", "app.py"]