"""
Validation utilities for Neo4j MCP server.

This module provides validation functions for various inputs
including Cypher queries, parameters, and data types.
"""

import re
from typing import Any, Dict, List, Optional


def validate_cypher_query(query: str) -> bool:
    """
    Basic validation for Cypher queries.
    
    Args:
        query: Cypher query string to validate
        
    Returns:
        True if query appears valid, False otherwise
    """
    if not query or not isinstance(query, str):
        return False
    
    # Remove extra whitespace
    query = query.strip()
    
    if not query:
        return False
    
    # Check for obvious SQL injection patterns
    dangerous_patterns = [
        r';\s*DROP\s+',
        r';\s*DELETE\s+',
        r';\s*ALTER\s+',
        r'--',
        r'/\*.*\*/',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False
    
    return True


def validate_username(username: str) -> bool:
    """
    Validate Neo4j username.
    
    Args:
        username: Username to validate
        
    Returns:
        True if username is valid, False otherwise
    """
    if not username or not isinstance(username, str):
        return False
    
    # Basic username validation
    if len(username) < 1 or len(username) > 50:
        return False
    
    # Allow alphanumeric, underscore, hyphen, dot
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return False
    
    return True


def validate_password(password: str) -> bool:
    """
    Validate Neo4j password.
    
    Args:
        password: Password to validate
        
    Returns:
        True if password is valid, False otherwise
    """
    if not password or not isinstance(password, str):
        return False
    
    # Basic password validation
    if len(password) < 1:
        return False
    
    return True


def validate_parameters(parameters: Dict[str, Any]) -> bool:
    """
    Validate query parameters.
    
    Args:
        parameters: Query parameters to validate
        
    Returns:
        True if parameters are valid, False otherwise
    """
    if not isinstance(parameters, dict):
        return False
    
    # Check parameter keys are valid
    for key in parameters.keys():
        if not isinstance(key, str) or not key:
            return False
        
        # Parameter keys should be valid identifiers
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            return False
    
    return True


def validate_node_label(label: str) -> bool:
    """
    Validate Neo4j node label.
    
    Args:
        label: Node label to validate
        
    Returns:
        True if label is valid, False otherwise
    """
    if not label or not isinstance(label, str):
        return False
    
    # Neo4j label naming rules
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', label):
        return False
    
    return True


def validate_property_name(property_name: str) -> bool:
    """
    Validate Neo4j property name.
    
    Args:
        property_name: Property name to validate
        
    Returns:
        True if property name is valid, False otherwise
    """
    if not property_name or not isinstance(property_name, str):
        return False
    
    # Neo4j property naming rules
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', property_name):
        return False
    
    return True


def sanitize_string_parameter(value: str) -> str:
    """
    Sanitize string parameter for Cypher queries.
    
    Args:
        value: String value to sanitize
        
    Returns:
        Sanitized string value
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove or escape potentially dangerous characters
    # This is basic sanitization - parameterized queries are preferred
    value = value.replace("'", "\\'")
    value = value.replace('"', '\\"')
    value = value.replace('\n', '\\n')
    value = value.replace('\r', '\\r')
    value = value.replace('\t', '\\t')
    
    return value


def validate_date_format(date_string: str) -> bool:
    """
    Validate date string format (YYYY-MM-DD).
    
    Args:
        date_string: Date string to validate
        
    Returns:
        True if date format is valid, False otherwise
    """
    if not isinstance(date_string, str):
        return False
    
    # Check YYYY-MM-DD format
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_string):
        return False
    
    # Basic range checks
    try:
        year, month, day = map(int, date_string.split('-'))
        
        if year < 1900 or year > 2100:
            return False
        if month < 1 or month > 12:
            return False
        if day < 1 or day > 31:
            return False
        
        return True
    except (ValueError, IndexError):
        return False


def validate_rating(rating: Any) -> bool:
    """
    Validate rating value (1-5).
    
    Args:
        rating: Rating value to validate
        
    Returns:
        True if rating is valid, False otherwise
    """
    try:
        rating_num = float(rating)
        return 1.0 <= rating_num <= 5.0
    except (TypeError, ValueError):
        return False


def validate_weight(weight: Any) -> bool:
    """
    Validate weight value (positive number).
    
    Args:
        weight: Weight value to validate
        
    Returns:
        True if weight is valid, False otherwise
    """
    try:
        weight_num = float(weight)
        return weight_num > 0 and weight_num < 1000  # Reasonable upper limit
    except (TypeError, ValueError):
        return False 