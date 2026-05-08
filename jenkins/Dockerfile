FROM jenkins/jenkins:2.555.1-lts

USER root

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear links simbólicos para python3 y pip3
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Instalar sonar-scanner CLI
RUN curl -sSLo /tmp/sonar-scanner.zip \
    https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-6.2.1.4610-linux-x64.zip \
    && unzip /tmp/sonar-scanner.zip -d /opt \
    && mv /opt/sonar-scanner-6.2.1.4610-linux-x64 /opt/sonar-scanner \
    && ln -s /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner \
    && rm /tmp/sonar-scanner.zip

# Configurar PATH para el usuario jenkins
ENV PATH="/usr/local/bin:/usr/bin:/bin:/usr/games:/usr/local/games:/opt/sonar-scanner/bin"

USER jenkins

EXPOSE 8080 50000