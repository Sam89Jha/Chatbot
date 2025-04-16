from flask import Flask, render_template, request, jsonify
import boto3
import os
import json
import uuid
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# AWS Clients
polly = boto3.client("polly")
translate = boto3.client("translate")
comprehend = boto3.client("comprehend")
bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")

# Language to Voice Mapping
voice_mapping = {
    "en": "Joanna",
    "zh": "Zhiyu",
    "ms": "Joanna",
    "th": "Joanna",
    "vi": "Joanna",
    "tl": "Joanna",
}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/send_text", methods=["POST"])
def send_text():
    data = request.get_json()
    text = data["text"]
    receiver_locale = data["receiver_locale"]
    sender = data["sender"]

    sentiment_response = comprehend.detect_sentiment(Text=text, LanguageCode="en")
    sentiment = sentiment_response["Sentiment"]

    translated_text = translate.translate_text(
        Text=text, SourceLanguageCode="auto", TargetLanguageCode=receiver_locale
    )["TranslatedText"]

    unique_id = str(uuid.uuid4())
    voice_id = voice_mapping.get(receiver_locale, "Joanna")
    response = polly.synthesize_speech(
        Text=translated_text, OutputFormat="mp3", VoiceId=voice_id
    )

    audio_stream = response["AudioStream"].read()
    audio_file = f"static/{sender}_text_output_{unique_id}.mp3"

    with open(audio_file, "wb") as file:
        file.write(audio_stream)

    return jsonify(
        {
            "audio": "/" + audio_file,
            "sentiment": sentiment,
            "original_text": text,
            "translated_text": translated_text,
        }
    )


@app.route("/send_image", methods=["POST"])
def send_image():
    file = request.files["image"]
    receiver_locale = request.form["receiver_locale"]
    tone = request.form.get("tone", "formal")
    sender = request.form["sender"]
    image_bytes = file.read()

    unique_id = str(uuid.uuid4())
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    if tone == "formal":
        user_instruction = (
            "You are a professional caption generator. "
            "Look at the image and write a formal 40-word description. "
            "Do not explain your answer. "
            "Start your response with: 'You received an image of...'"
        )
    elif tone == "casual":
        user_instruction = (
            "Look at the image and give a casual 40-word description. "
            "No explanation, no lead-in. Just start with: 'You received an image of...'"
        )
    elif tone == "funny":
        user_instruction = (
            "Write a funny 40-word caption describing the image. "
            "Avoid any intro or notes. Directly start with: 'You received an image of...'"
        )
    else:
        user_instruction = (
            "Look at the image and describe it creatively in 40 words. "
            "Do not add anything before. Begin directly with: 'You received an image of...'"
        )

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": encoded_image,
                        },
                    },
                    {"type": "text", "text": user_instruction},
                ],
            }
        ],
        "max_tokens": 500,
    }

    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

    response = bedrock.invoke_model(
        body=json.dumps(payload),
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
    )

    output = json.loads(response["body"].read())
    final_text = output["content"][0]["text"]

    sentiment_response = comprehend.detect_sentiment(Text=final_text, LanguageCode="en")
    sentiment = sentiment_response["Sentiment"]

    translated_text = translate.translate_text(
        Text=final_text, SourceLanguageCode="auto", TargetLanguageCode=receiver_locale
    )["TranslatedText"]

    voice_id = voice_mapping.get(receiver_locale, "Joanna")
    speech_response = polly.synthesize_speech(
        Text=translated_text, OutputFormat="mp3", VoiceId=voice_id
    )

    audio_stream = speech_response["AudioStream"].read()

    audio_file = f"static/{sender}_image_output_{unique_id}.mp3"
    image_filename = f"static/{sender}_uploaded_image_{unique_id}.jpg"

    with open(audio_file, "wb") as file:
        file.write(audio_stream)

    with open(image_filename, "wb") as img_file:
        img_file.write(image_bytes)

    return jsonify(
        {
            "audio": "/" + audio_file,
            "sentiment": sentiment,
            "original_text": final_text,
            "translated_text": translated_text,
            "image": "/" + image_filename,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
