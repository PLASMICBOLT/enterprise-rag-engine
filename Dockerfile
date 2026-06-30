# 1. Start with a lightweight Linux image that already has Python 3.10 installed
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy your requirements file into the container
COPY requirements.txt .

# 4. Install the dependencies inside the container
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your Python files into the container
COPY . .

# 6. Expose the port FastAPI uses
EXPOSE 8000

# 7. The command to start the server when the container boots
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]