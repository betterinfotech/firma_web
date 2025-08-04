from datadog import statsd


def track_success():
    try:
        statsd.increment("flask.task.completed", tags=["env:dev", "result:success"])
    except Exception as e:
        print("Datadog statsd failed:", e)
