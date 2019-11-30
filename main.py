import time
import datetime
from urllib.parse import quote
import requests
from alertmanager import AlertManager
from alertmanager import Alert
import pprint

ALETRMANAGER_HOST = "http://prometheus-alertmanager"
ALETRMANAGER_PORT ="80"
LOKI_URL = "http://loki:3100/loki/api/v1/"
#LOKI_URL = "http://localhost:3100/loki/api/v1/"
GRAFANA_LINK = "https://grafana.example.ru"

def sender(data):
    host = ALETRMANAGER_HOST
    port = ALETRMANAGER_PORT
    alert = Alert.from_dict(data)
    a_manager = AlertManager(host=host, port=port)
    a_manager.post_alerts(alert)

def get_query():
    # get current time, get ms for link and ns for query
    t0 = datetime.datetime.now()
    start_time = t0 - datetime.timedelta(minutes=1)
    start_timestamp_ms = int(start_time.timestamp()) * 1000
    end_timestamp_ms = int(t0.timestamp()) * 1000
    start_timestamp_ns = int(start_time.timestamp()) * 1000000000
    end_timestamp_ns = int(t0.timestamp()) * 1000000000

    # query example: {app="app",level!~"Info"}
    query = 'query={platform="nw",level!~"Info|Debug|null|"}'
    start = "&start={}".format(start_timestamp_ns)
    end = "&end={}".format(end_timestamp_ns)
    url = "{}query_range?{}{}{}".format(LOKI_URL, query, start, end)
    r_json = requests.get(url).json()

    for result in r_json["data"]["result"]:
        error_num = len(result["values"])
        instance = result["stream"]["instance"]
        level = result["stream"]["level"]
        app_kubernetes_io_name = result["stream"]["app_kubernetes_io_name"]
        link = quote('%s/explore?orgId=1&left=["%s","%s","Loki",{"expr":"{app_kubernetes_io_name=\\"%s\\",level=\\"%s\\"}"},{"mode":"Logs"},{"ui":[true,true,true,"none"]}]' % (GRAFANA_LINK, start_timestamp_ms, end_timestamp_ms, app_kubernetes_io_name, level), safe='/:[]?&,}{=')
        data = get_data(instance, app_kubernetes_io_name, link, error_num, level, start_time, t0)

        sender(data)
        #pprint.pprint(result["values"])
        return "{} {} has {} {}(s)".format(t0.strftime("%b %d %X"), app_kubernetes_io_name, error_num, level)

def get_data(instance, app, link, error_num, level, start_at, end):
    # set color for alert
    if level == "Error":
        color = "#e0370b"
    elif level == "Critical":
        color = "#ff0000"
        level = level.upper()
    elif level == "Warning":
        color = "#e0a50a"
    else:
        color = "#9400d3"

    data = {
        "labels": {
            "app_kubernetes_io_name": app,
            "instance": instance,
            "level": level,
            "severity": "alertina",
            "color": color
        },
        "annotations": {
            "title": "{} in {}".format(level, app),
            "description": "{} has {} {}(s) in last 1 minute".format(instance, error_num, level),
            "time": "{} - {}".format(start_at.strftime("%A %X"), end.strftime("%X")),
            "link": link
        }
    }

    return data

def main():
    try:
        log = get_query()
        print(log)
    except requests.ConnectionError as e:
        print(e)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(60)
