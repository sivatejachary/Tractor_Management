# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy project files to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 7860

# Run the application with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
