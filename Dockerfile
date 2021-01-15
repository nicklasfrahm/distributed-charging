# Define image during build.
FROM python:3-slim AS build

# Define the source file to be used.
ARG SRC_FILE

# Configure working directory.
WORKDIR /app

# Install dependencies.
ADD requirements.txt .
RUN pip install -r requirements.txt

# Add source file.
ADD $SRC_FILE ./app.py

# Define environment variables.
ENV BROKER_URI=

# Define command to start application.
CMD python3 ./app.py $BROKER_URI
