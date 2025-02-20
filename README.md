# BlackBox-Monitoring

Descrizione

Questo progetto automatizza l'aggiunta di URL da un file JSON alla configurazione di Blackbox Exporter e Prometheus, consentendo il monitoraggio dinamico di endpoint HTTP.

## Prerequisiti

- Una macchina con Rocky Linux (o distribuzione equivalente)
- Permessi di root o sudo
- Connessione a Internet per scaricare i pacchetti necessari
- Python installato sul sistema


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
## 2. Creare il File JSON con le URLs

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
### 3. Creare uno script python

```
vim add_targets.py

```
```
import yaml
import json

# Percorsi dei file
json_file_path = '/root/urls.json'
prometheus_yml_path = '/etc/prometheus/prometheus.yml'

# Leggi il file JSON
with open(json_file_path, 'r') as json_file:
    urls_data = json.load(json_file)

# Leggi il file prometheus.yml
with open(prometheus_yml_path, 'r') as yml_file:
    prometheus_yml = yaml.safe_load(yml_file)

# Estrarre i target esistenti
scrape_configs = prometheus_yml.get('scrape_configs', [])
blackbox_config = next((job for job in scrape_configs if job['job_name'] == 'blackbox'), None)

if not blackbox_config:
    blackbox_config = {
        'job_name': 'blackbox',
        'metrics_path': '/probe',
        'params': {'module': ['http_2xx']},
        'static_configs': [],
        'relabel_configs': [
            {'source_labels': ['__address__'], 'target_label': '__param_target'},
            {'source_labels': ['__param_target'], 'target_label': 'instance'},
            {'target_label': '__address__', 'replacement': '192.168.3.99:9115'}
        ]
    }
    scrape_configs.append(blackbox_config)

# Combina i target esistenti con quelli nuovi
existing_targets = [target for config in blackbox_config['static_configs'] for target in config['targets']]
new_targets = [url['url'] for url in urls_data['urls']]
combined_targets = list(set(existing_targets + new_targets))  # Rimuovi i duplicati

# Aggiorna la configurazione con i nuovi target
blackbox_config['static_configs'] = [{'targets': combined_targets}]

# Scrivi il file prometheus.yml aggiornato mantenendo la struttura
with open(prometheus_yml_path, 'w') as yml_file:
    yaml.safe_dump(prometheus_yml, yml_file, sort_keys=False)

print(f'Le URL sono state aggiunte correttamente a {prometheus_yml_path}')
```

## 4. Eseguire un Container Nginx con Podman

### 1) Avvio container nginx che ascolta sulla porta 8080
```
podman run -d --name nginx-container -p 8080:80 nginx

```

## 5. Installazione e Configurazione di Prometheus

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
http://localhost:9090/graph
```
```
probe_http_status_code
```
Questa query mostrerà i codici di stato HTTP delle URLs monitorate.
