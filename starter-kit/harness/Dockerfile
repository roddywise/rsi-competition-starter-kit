FROM python:3.12-alpine3.20

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BASELINE_CPU_THREADS=1 \
    RSI_TASKS_ROOT=/app/tasks \
    PYTHONPATH=/opt/contest-harness-sdk-1.0.4

RUN apk add --no-cache libstdc++

WORKDIR /opt
COPY harness/vendor/contest-harness-sdk-1.0.4.tar.gz /tmp/contest-harness-sdk-1.0.4.tar.gz
RUN echo "7afd282d6b5fd889d64d0515a67d169806970e36200689b18d2040026167a4af  /tmp/contest-harness-sdk-1.0.4.tar.gz" \
    | sha256sum -c - \
    && tar -xzf /tmp/contest-harness-sdk-1.0.4.tar.gz -C /opt \
    && python -m pip install --no-cache-dir numpy==1.26.4 \
    && rm -f /tmp/contest-harness-sdk-1.0.4.tar.gz

WORKDIR /app
COPY harness/app/harness.py /app/harness.py
COPY harness/app/contest_submission.py /app/contest_submission.py
COPY harness/app/drift.py /app/drift.py
COPY harness/app/task_a/__init__.py /app/task_a/__init__.py
COPY harness/app/task_b/__init__.py /app/task_b/__init__.py
COPY harness/app/task_c/__init__.py /app/task_c/__init__.py

COPY tasks/A-gas/baselines /app/tasks/A-gas/baselines
COPY tasks/B-bearing/baselines /app/tasks/B-bearing/baselines
COPY tasks/C-engine/baselines /app/tasks/C-engine/baselines

RUN mkdir -p /workspace && chown 65534:65534 /workspace

USER 65534:65534
ENTRYPOINT ["python3", "/app/harness.py"]
