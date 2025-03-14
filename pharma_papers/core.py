from typing import List, Dict
import requests
import xmltodict
import csv
import re

class PubMedFetcher:
    """Core class to fetch and process PubMed papers."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def __init__(self, debug: bool = False):
        self.debug = debug

    def search_papers(self, query: str, max_results: int = 100) -> List[str]:
        """Search PubMed for paper IDs based on query."""
        url = f"{self.BASE_URL}esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&retmode=json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if self.debug:
            print(f"Found {len(data['esearchresult']['idlist'])} papers for query '{query}'")
        return data["esearchresult"]["idlist"]

    def fetch_paper_details(self, pubmed_ids: List[str]) -> List[Dict]:
        """Fetch detailed information for given PubMed IDs."""
        if not pubmed_ids:
            return []

        url = f"{self.BASE_URL}efetch.fcgi?db=pubmed&id={','.join(pubmed_ids)}&retmode=xml"
        response = requests.get(url)
        response.raise_for_status()
        data = xmltodict.parse(response.content)

        articles = data["PubmedArticleSet"]["PubmedArticle"]
        if not isinstance(articles, list):
            articles = [articles]

        return self._process_articles(articles)
    def _is_pharma_affiliated(self, affiliation: str) -> bool:
        """Identify pharmaceutical/biotech affiliations."""
        academic_keywords = {"university", "college", "institute", "hospital", "school", "research center"}
        
        pharma_keywords = {"pharma", "biotech", "inc.", "ltd.", "therapeutics", 
                        "biosciences", "biopharma", "lifesciences", "medicines", 
                        "oncology", "genomics", "drug research", "medical research",
                        "sanofi", "novo nordisk", "eli lilly", "astrazeneca", "bayer",
                        "pfizer inc.", "novartis pharmaceuticals", "merck & co., inc."}

        lower_aff = affiliation.lower()
        
        # Ensure we check full company names, not just split words
        if any(keyword in lower_aff for keyword in pharma_keywords) and not any(keyword in lower_aff for keyword in academic_keywords):
            return True
        return False
 #  Ensures return type is boolean


    def _process_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process articles to extract required fields."""
        results = []
        for article in articles:
            try:
                medline = article["MedlineCitation"]
                pubmed_id = medline["PMID"]["#text"]
                title = medline["Article"]["ArticleTitle"]
                pub_date = medline["Article"]["Journal"]["JournalIssue"]["PubDate"]
                pub_date_str = f"{pub_date.get('Year', 'N/A')}-{pub_date.get('Month', 'N/A')}"

                authors = medline["Article"].get("AuthorList", {}).get("Author", [])
                if not isinstance(authors, list):
                    authors = [authors]

                pharma_authors = []
                affiliations = []
                email = None

                for author in authors:
                    last_name = author.get("LastName", "Unknown")
                    initials = author.get("Initials", "")
                    full_name = f"{last_name} {initials}".strip()

                    aff_info = author.get("AffiliationInfo", {})
                    affiliation = aff_info.get("Affiliation", "N/A") if isinstance(aff_info, dict) else "N/A"

                    if self.debug:
                        print(f"Checking: {full_name} -> {affiliation}")

                    email_match = re.search(r'[\w\.-]+@[a-zA-Z\.-]+\.[a-zA-Z]+', affiliation)
                    if email_match:
                        email = email_match.group(0)

                    if self._is_pharma_affiliated(affiliation):
                        pharma_authors.append(full_name)
                        affiliations.append(affiliation)

                if pharma_authors:
                    results.append({
                        "PubmedID": pubmed_id,
                        "Title": title,
                        "Publication Date": pub_date_str,
                        "Non-academic Author(s)": "; ".join(pharma_authors),
                        "Company Affiliation(s)": "; ".join(affiliations),
                        "Corresponding Author Email": email or "N/A"
                    })
            except KeyError as e:
                if self.debug:
                    print(f"Error processing article {pubmed_id}: {e}")

        return results

    def save_to_csv(self, results: List[Dict], filename: str) -> None:
        """Save results to a CSV file."""
        if not results:
            print("No results to save.")
            return

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        if self.debug:
            print(f"Saved {len(results)} pharma/biotech-affiliated papers to {filename}")
