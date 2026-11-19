import asyncio
import json

from app.services.analysis_service import process_link_analysis


async def main():
    url = "https://chatgpt.com/"

    try:
        print(f"Executing link analysis for: {url}...")

        result = await process_link_analysis(url)

        print("\nAI ANALYSIS SUCCESSFUL")
        print("=" * 60)

        print(result.model_dump_json(indent=2))

        # Save output for inspection
        with open("sample_analysis.json", "w", encoding="utf-8") as file:
            json.dump(
                result.model_dump(mode="json"),
                file,
                indent=2,
                ensure_ascii=False
            )

        print("\nSaved result to sample_analysis.json")

    except Exception as error:
        print("\nERROR:", type(error).__name__, str(error))


if __name__ == "__main__":
    asyncio.run(main())
