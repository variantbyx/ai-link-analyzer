from app.schemas import LinkRequest

# Test valid URL
request = LinkRequest(
    url="https://google.com"
)

print("Valid URL:", request.url)

# Test invalid URL
try:
    LinkRequest(url="not-a-valid-url")
except Exception as error:
    print("\nInvalid URL correctly rejected:")
    print(error)

# Inspect the expected AI output structure
from app.schemas import LinkAnalysisResponse

schema = LinkAnalysisResponse.model_json_schema()

print("\nExpected response structure:")
print(schema.keys())

print("\nAll schema tests completed!")