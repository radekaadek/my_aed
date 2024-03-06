#!/bin/bash
# CMD ["./refresh_model.sh", "&", "uvicorn", "serve_results:app", "--host", "0.0.0.0", "--port", "8080"]
./refresh_model.sh &
uvicorn serve_results:app --host 0.0.0.0 --port 8080

