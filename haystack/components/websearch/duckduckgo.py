import logging
from typing import Any, Dict, List, Optional

from haystack import (
    Document,
    component,
    default_from_dict,
    default_to_dict,
)
from haystack.lazy_imports import LazyImport

with LazyImport(
    "Run 'pip install duckduckgo_search' to install the package."
) as duckduckgo_import:
    from duckduckgo_search import DDGS


logger = logging.getLogger(__name__)


@component
class DuckDuckGoWebSearch:
    """
    Search engine using DuckDockGo API through `duckduckgo_search` package.
    Given a query, it returns a list of URLs that are the most relevant.
    """

    def __init__(  # noqa: PLR0913
        self,
        top_k: Optional[int] = 10,
        timeout: int = 10,
        headers: Optional[Any] = None,
        proxies: Optional[Any] = None,
        search_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        :param top_k: Number of documents to return.
        :param search_params: Additional parameters passed to the DuckDockGo API.
        """
        self.top_k = top_k
        self.timeout = timeout
        self.headers = headers
        self.proxies = proxies
        self.search_params = search_params or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize this component to a dictionary.
        """
        return default_to_dict(
            self,
            top_k=self.top_k,
            timeout=self.timeout,
            headers=self.headers,
            proxies=self.proxies,
            search_params=self.search_params,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DuckDuckGoWebSearch":
        """
        Deserialize this component from a dictionary.
        """
        return default_from_dict(cls, data)

    @component.output_types(documents=List[Document], links=List[str])
    def run(self, query: str) -> dict[str, Any]:
        """
        Search the DuckDockGo API for the given query and return the results as a list of Documents and a list of links.

        :param query: Query string.
        """
        ddgs = DDGS(timeout=self.timeout, headers=self.headers, proxies=self.proxies)

        safe_search = self.search_params.pop("safesearch", "moderate")
        region = self.search_params.pop("region", "wt-wt")

        documents: List[Document] = []
        links: List[str] = []

        results = list(
            ddgs.text(
                query,
                max_results=self.top_k,
                safesearch=safe_search,
                region=region,
                backend="api",
            )
        )

        for result in results:
            documents.append(
                Document.from_dict(
                    {
                        "title": result.get("title", ""),
                        "content": result.get("answer", ""),
                        "link": result.get("href", ""),
                    }
                ),
            )
            links.append(result.get("href", ""))

        logger.debug(
            "DuckDuckGoWebSearch returned %s documents for the query '%s'",
            len(documents),
            query,
        )

        return {"documents": documents, "links": links}
