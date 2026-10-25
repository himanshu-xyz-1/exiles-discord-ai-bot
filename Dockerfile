FROM python:3.11-slim

# Create a non-root user for security (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Install dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY --chown=user:user . .

USER user
EXPOSE 7860

CMD ["python", "bot.py"]
