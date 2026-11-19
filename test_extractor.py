import asyncio
from app.services.website_extractor import extract_website


async def main():
    url = "https://walmart.com"

    try:
        result = await extract_website(url)

        print("\nWEBSITE EXTRACTION SUCCESSFUL")
        print("-" * 50)

        print("URL:", result["url"])
        print("TITLE:", result["title"])
        print("DESCRIPTION:", result["description"])
        print("HEADINGS:", result["headings"])

        print("\nCONTENT:")
        print(result["content"])

        print("\nLINKS:")
        print(result["links"])

    except Exception as e:
        print("ERROR:", str(e))


if __name__ == "__main__":
    asyncio.run(main())