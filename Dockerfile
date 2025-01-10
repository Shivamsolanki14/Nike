FROM python:3.9-slim

# Set working directory
WORKDIR /NIKE

# Create logs directory
RUN mkdir -p logs

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a volume for configuration
VOLUME /NIKE/config

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "src/main.py"] 