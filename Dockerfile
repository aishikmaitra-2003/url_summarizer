FROM python:3.10-slim

WORKDIR /app

# Avoid Python cache issues
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Streamlit runs on 8501
EXPOSE 8501

# Run app properly
# CMD ["streamlit", "run", "yt_tester.py", "--server.port=8501", "--server.address=0.0.0.0"]
CMD ["sh", "-c", "streamlit run lang_summarizer.py --server.port=$PORT --server.address=0.0.0.0"]
