import json, logging, datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k not in ('name','msg','args','levelname','levelno','pathname','filename','module',
                         'exc_info','exc_text','stack_info','lineno','funcName','created','msecs',
                         'relativeCreated','thread','threadName','process','processName'): 
                log_record[k] = v
            #
            log_record.update(record.extra)
        return json.dumps(log_record)

def setup_logger():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    return root
