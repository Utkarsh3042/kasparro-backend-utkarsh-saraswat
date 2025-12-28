from typing import List, Dict, Any
from math import ceil
from src.models.schemas import PaginationMeta

def create_pagination_meta(
    page: int,
    page_size: int,
    total_items: int
) -> PaginationMeta:
    """
    Create pagination metadata
    
    Args:
        page: Current page number
        page_size: Items per page
        total_items: Total number of items
        
    Returns:
        PaginationMeta object with pagination info
    """
    total_pages = ceil(total_items / page_size) if total_items > 0 else 0
    
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )


def paginate_list(
    items: List[Any],
    page: int,
    page_size: int
) -> Dict[str, Any]:
    """
    Paginate a list of items
    
    Args:
        items: List of items to paginate
        page: Current page number
        page_size: Items per page
        
    Returns:
        Dictionary with paginated data and metadata
    """
    total_items = len(items)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_items = items[start_idx:end_idx]
    pagination_meta = create_pagination_meta(page, page_size, total_items)
    
    return {
        "data": paginated_items,
        "pagination": pagination_meta.dict()
    }


def get_pagination_links(
    base_url: str,
    page: int,
    page_size: int,
    total_pages: int
) -> Dict[str, str]:
    """
    Generate pagination links for HATEOAS
    
    Args:
        base_url: Base URL for the endpoint
        page: Current page
        page_size: Items per page
        total_pages: Total number of pages
        
    Returns:
        Dictionary with pagination links
    """
    links = {
        "self": f"{base_url}?page={page}&page_size={page_size}",
        "first": f"{base_url}?page=1&page_size={page_size}",
        "last": f"{base_url}?page={total_pages}&page_size={page_size}"
    }
    
    if page > 1:
        links["previous"] = f"{base_url}?page={page-1}&page_size={page_size}"
    
    if page < total_pages:
        links["next"] = f"{base_url}?page={page+1}&page_size={page_size}"
    
    return links