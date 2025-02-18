# BlackBox-Monitoring

Analizzare un json contenente delle URLs (con annessi i parametri di una chiamata HTTP) e che aggiunga sul BlackBox export le url da monitorar con Prometheus.


Descrizione
Il progetto ha l'obiettivo di analizzare un json contenente delle URLs (con annessi i parametri di una chiamata HTTP) e che aggiunga sul BlackBox export le url da monitorar con Prometheus. 


## Prerequisiti

- Una macchina con Rocky Linux (o distribuzione equivalente)
- Permessi di root o sudo
- Connessione a Internet per scaricare i pacchetti necessari


## 1. Installazione di BlackBox_exporter

### 1) Installa BlackBox sulla VM Rocky Linux:
``` 
wget https://github.com/prometheus/blackbox_exporter/releases/download/v0.19.0/blackbox_exporter-0.19.0.linux-amd64.tar.gz
tar -xvzf blackbox_exporter-0.19.0.linux-amd64.tar.gz
mv blackbox_exporter-0.19.0.linux-amd64/blackbox_exporter /usr/local/bin/
mkdir /etc/blackbox_exporter/
mv blackbox_exporter-0.19.0.linux-amd64/blackbox.yml /etc/blackbox_exporter/

```
### 2) Creazione utente blackbox_exporter
```
useradd --no-create-home --shell /bin/false blackbox
```

### 3) Creazione del servizio blackbox_exporter
```
vim /etc/systemd/system/blackbox_exporter.service
```
```
[Unit]
Description=BlackBox Exporter
After=network.target

[Service]
User=blackbox
ExecStart=/usr/local/bin/blackbox_exporter --config.file=/etc/blackbox_exporter/blackbox.yml
Restart=on-failure

[Install]
WantedBy=multi-user.target

```

### 4) Avviare e Abilitare Blackbox_exporter:
```
sudo systemctl daemon-reload
sudo systemctl enable blackbox_exporter
sudo systemctl start blackbox_exporter
sudo systemctl status blackbox_exporter
```
## 2. Installazione di Ansible
   
### 1) Scarica e Installa Ansible
```   
dnf install -y epel-release
dnf install -y ansible

```
### 2) Creare una Directory di Progetto
``` 
mkdir -p ~/ansible_project/{roles/add_urls/tasks,file}
cd ~/ansible_project

```
### 3) Creare il File JSON con le URLs

```
vim file/urls.json
```
```
{

  "urls": [
     {
       "url": "http://localhost:8080",
       "method": "GET"

     }
 ]
}
```
### 4) Creare il Playbook Ansible

```
vim add_urls.yml

```
```
- name: Add URLs to BlackBox Exporter
  hosts: localhost
  roles:
    - add_urls
```

### 5) Creare il File di Ruolo Ansible per Parsare il JSON

```
vim roles/add_urls/tasks/main.yml

```
```
- name: Read URLs from JSON
  ansible.builtin.slurp:
    src: file/urls.json
  register: json_content

- name: Parse JSON
  set_fact:
    urls: "{{ json_content.content | b64decode | from_json }}"

- name: Add URLs to BlackBox Exporter
  debug:
    msg: "Adding URL: {{ item.url }} with method {{ item.method }}"
  loop: "{{ urls['urls'] }}"
```

## 3. Eseguire un Container Nginx con Podman

### 1) Avvio container nginx che ascolta sulla porta 8080
```
podman run -d --name nginx-container -p 8080:80 nginx

```

## 4. Installazione e Configurazione di Prometheus

### 1) Scarica e Installa Prometheus:
```   
wget https://github.com/prometheus/prometheus/releases/download/v2.31.1/prometheus-2.31.1.linux-amd64.tar.gz
tar xvfz prometheus-2.31.1.linux-amd64.tar.gz
mv prometheus-2.31.1.linux-amd64/prometheus /usr/local/bin/
mv prometheus-2.31.1.linux-amd64/promtool   /usr/local/bin/
mkdir /etc/prometheus
mkdir /var/lib/prometheus
```
### 2) Creazione utente Prometheus

```
useradd --no-create-home --shell /bin/false prometheus
```

### 3) Configurazione di Prometheus:
```
vim /etc/prometheus/prometheus.yml
```
``` 
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
        - http://localhost:8080
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9115

```
### 4) Creazione del Servizio Systemd per Prometheus:
```
vim /etc/systemd/system/prometheus.service
```
``` 
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
--config.file=/etc/prometheus/prometheus.yml \
--storage.tsdb.path=/var/lib/prometheus/ \
--web.console.templates=/etc/prometheus/consoles \
--web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
```
### 5) Avviare e Abilitare Prometheus
 ```  
systemctl daemon-reload
systemctl start prometheus
systemctl enable prometheus
```

## 6. Verificare il Funzionamento

### 1) Verifica che BlackBox Exporter sia in Esecuzione

Dovresti vedere le metriche esposte.

```
http://localhost:9115/metrics
```

### 2) Controlla i Targets di Prometheus
```
http://192.168.3.76:9090/targets
```
Dovresti vedere il job blackbox con lo stato "UP".

### 3) Esegui una query su prometheus
```
http://192.168.3.76:9090/graph
```
```
probe_http_status_code
```
Questa query mostrerà i codici di stato HTTP delle URLs monitorate.
