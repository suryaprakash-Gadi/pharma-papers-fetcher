import click
from typing import Optional
from tabulate import tabulate
from .core import PubMedFetcher

@click.command()
@click.argument("query")
@click.option("-d", "--debug", is_flag=True, help="Print debug information")
@click.option("-f", "--file", type=str, help="Output CSV filename")
@click.option("--max-results", type=int, default=100, help="Number of results to fetch")
def main(query: str, debug: bool, file: Optional[str], max_results: int) -> None:
    """Fetch PubMed papers with pharmaceutical/biotech affiliations."""
    fetcher = PubMedFetcher(debug=debug)
    try:
        pubmed_ids = fetcher.search_papers(query, max_results)
        if not pubmed_ids:
            print("No papers found for the given query.")
            return
        
        results = fetcher.fetch_paper_details(pubmed_ids)
        if file:
            fetcher.save_to_csv(results, file)
        else:
            if not results:
                print("No pharma/biotech-affiliated papers found.")
            else:
                print(tabulate(results, headers="keys", tablefmt="grid"))
    except Exception as e:
        print(f"Failed to process query '{query}': {e}")
        if debug:
            raise

if __name__ == "__main__":
    main()
