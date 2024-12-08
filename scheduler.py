from datetime import datetime, timedelta
class ScheduledTask:
    def __init__(self, func, interval_seconds, name=None, *args, **kwargs):
        self.func = func
        self.interval = interval_seconds
        self.last_run = datetime.min
        self.name = name or func.__name__
        self.args = args
        self.kwargs = kwargs

    def should_run(self):
        return datetime.now() - self.last_run > timedelta(seconds=self.interval)

    def run(self):
        try:
            print(f"\nRunning task: {self.name}")
            self.func(*self.args, **self.kwargs)
            self.last_run = datetime.now()
            
        except Exception as e:
            print(f"Error in task {self.name}: {e}")
            self.last_run = datetime.now()