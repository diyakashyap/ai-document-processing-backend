import json

import boto3

from app.core.config import settings


def get_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def summarize_text(extracted_text: str) -> str:
    if not extracted_text.strip():
        return "No readable text was found in this document."

    prompt = (
        "Summarize the following document in clear, concise business language. "
        "Include key points, obligations, dates, risks, and recommended follow-up actions if present.\n\n"
        f"Document text:\n{extracted_text[:50000]}"
    )

    body = {
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        "inferenceConfig": {
            "maxTokens": settings.bedrock_max_tokens,
            "temperature": settings.bedrock_temperature,
        },
    }

    response = get_bedrock_client().invoke_model(
        modelId=settings.bedrock_model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    payload = json.loads(response["body"].read())
    return payload["output"]["message"]["content"][0]["text"]
