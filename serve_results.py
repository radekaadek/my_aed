import fastapi
import uvicorn
from os import path

# serve the /results/results.json file
app = fastapi.FastAPI()

@app.get("/")
async def read_results():
    # check if the file exists
    if not path.exists("results/results.json"):
        return fastapi.responses.JSONResponse(status_code=503, content={"error": "Results are not ready yet or there was an error."})
    return fastapi.responses.FileResponse("results/results.json")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
