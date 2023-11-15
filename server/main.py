# Import libraries used for the server to receive files from the client
from typing import Annotated
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

# Choose speaker recognition and speech recognition model
from SpeechRecognition.SpeechBrain import SpeechBrain as Speech
from SpeakerRecognition.SpeechBrain import SpeechBrain as Speaker

# Create a FastAPI instance
app = FastAPI()
# Create instances of the models
speech = Speech()
speaker = Speaker()


# TODO: fix, stolen from https://fastapi.tiangolo.com/tutorial/request-files/
@app.post("/files/")
async def create_files(
    files: Annotated[list[bytes], File(description="Multiple files as bytes")],
):
    return {"file_sizes": [len(file) for file in files]}


async def get_text(audio):
    return await speech.get_text(audio)


async def get_speaker(audio):
    return await speaker.recognize(audio)


@app.post("/uploadfiles/")
async def create_upload_files(
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    return {"filenames": [file.filename for file in files]}


@app.get("/")
async def main():
    content = """
<body>
<form action="/files/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
<form action="/uploadfiles/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)