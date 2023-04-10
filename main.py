import copy
import asyncio
import requests

from fastapi import FastAPI, Request
from llama_cpp import Llama
from sse_starlette import EventSourceResponse

# load the model
print("Loading model...")
#llm = Llama(model_path="./models/ggml-vicuna-13b-4bit-rev1.bin")
llm = Llama(model_path="./models/ggml2-alpaca-7b-q4.bin")

print("Model loaded!")

app = FastAPI()

@app.get("/")
async def hello():
    return {"hello": "wooooooorld"}

@app.get("/model")
async def model():
    stream = llm(
        "Question: Who is Ada Lovelace? Answer: ",
        max_tokens=100,
        stop=["\n", " Q:"],
        echo=True,
    )

    result = copy.deepcopy(stream)
    return {"result": result}

@app.get("/jokes")
async def jokes(request: Request):
    def get_messages():
        url = "https://official-joke-api.appspot.com/random_ten"
        response = requests.get(url)
        if response.status_code == 200:
            jokes = response.json()
            messages = []
            for joke in jokes:
                setup = joke['setup']
                punchline = joke['punchline']
                message = f"{setup} {punchline}"
                messages.append(message)
            return messages
        else:
            return None
    
    async def sse_event():
        while True:
            if await request.is_disconnected():
                break

            for message in get_messages():
                yield {"data": message}

            await asyncio.sleep(1)
    
    return EventSourceResponse(sse_event())

@app.get("/llama")
async def llama(request: Request):
    stream = llm(
        "Question: Who is Ada Lovelace? Answer: ",
        max_tokens=100,
        stop=["\n", " Q:"],
        stream=True,
    )

    async def async_generator():
        for item in stream:
            yield item
    
    async def server_sent_events():
        async for item in async_generator():
            if await request.is_disconnected():
                break

            result = copy.deepcopy(item)
            text = result["choices"][0]["text"]

            yield {"data": text}

    return EventSourceResponse(server_sent_events())