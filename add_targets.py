import yaml
import json

# Percorsi dei file
json_file_path = '/opt/blackbox-monitoring/data/urls.json'
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
            {'target_label': '__address__', 'replacement': 'ip-server:9115'}
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
